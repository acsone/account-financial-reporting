import re
from collections import defaultdict

from openerp.osv import expression
from openerp import pooler
from openerp.tools.safe_eval import safe_eval


MODE_VARIATION = 'p'
MODE_INITIAL = 'i'
MODE_END = 'e'


class AccountingExpressionProcessor(object):
    """ Processor for accounting expressions.

    Expressions of the form <field><mode>[accounts][optional move line domain]
    are supported, where:
        * field is bal, crd, deb
        * mode is i (initial balance), e (ending balance),
          p (moves over period)
        * accounts is a list of accounts, possibly containing % wildcards
        * an optional domain on analytic lines allowing filters on eg analytic
          accounts or journal

    Examples:
        * bal[70]: balance of moves on account 70 over the period
          (it is the same as balp[70]);
        * bali[70,60]: initial balance of accounts 70 and 60;
        * bale[1%]: balance of accounts starting with 1 at end of period.

    How to use:
        * repeatedly invoke parse_expr() for each expression containing
          accounting variables as described above; this let the processor
          group domains and modes and accounts;
        * when all expressions have been parsed, invoke done_parsing()
          to notify the processor that it can prepare to query (mainly
          search all accounts - children, consolidation - that will need to
          be queried;
        * for each period, call do_queries(), then call replace_expr() for each
          expression to replace accounting variables with their resulting value
          for the given period.

    How it works:
        * by accumulating the expressions before hand, it ensure to do the
          strict minimum number of queries to the database (for each period,
          one query per domain and mode);
        * it queries using the orm read_group which reduces to a query with
          sum on debit and credit and group by on account_id (note: it seems
          the orm then does one query per account to fetch the account
          name...);
        * additionally, one query per view/consolidation account is done to
          discover the children accounts.
    """

    ACC_RE = re.compile(r"(?P<field>\bbal|\bcrd|\bdeb)"
                        r"(?P<mode>[pise])?"
                        r"(?P<accounts>_[0-9]+|\[.*?\])"
                        r"(?P<domain>\[.*?\])?")

    def __init__(self, cursor):
        self.pool = pooler.get_pool(cursor.dbname)
        # before done_parsing: {(domain, mode): set(account_codes)}
        # after done_parsing: {(domain, mode): set(account_ids)}
        self._map_account_ids = defaultdict(set)
        self._set_all_accounts = set()  # set((domain, mode))
        self._account_ids_by_code = defaultdict(set)

    def _load_account_codes(self, cr, uid, account_codes, account_domain,
                            context=None):
        account_obj = self.pool['account.account']
        exact_codes = set()
        like_codes = set()
        for account_code in account_codes:
            if account_code in self._account_ids_by_code:
                continue
            if '%' in account_code:
                like_codes.add(account_code)
            else:
                exact_codes.add(account_code)
        for account_id in account_obj.\
                search(cr, uid,
                       [('code', 'in', list(exact_codes))] + account_domain,
                       context=context):
            account = account_obj.browse(cr, uid, account_id, context=context)
            if account.type in ('view', 'consolidation'):
                self._account_ids_by_code[account.code].update(
                    account_obj._get_children_and_consol(
                        cr, uid,
                        [account.id],
                        context=context))
            else:
                self._account_ids_by_code[account.code].add(account.id)
        for like_code in like_codes:
            for account_id in account_obj.\
                    search(cr, uid,
                           [('code', 'like', like_code)] + account_domain,
                           context=context):
                account = account_obj.browse(cr, uid, account_id,
                                             context=context)
                if account.type in ('view', 'consolidation'):
                    self._account_ids_by_code[like_code].update(
                        account_obj._get_children_and_consol(
                            cr, uid,
                            [account.id],
                            context=context))
                else:
                    self._account_ids_by_code[like_code].add(account.id)

    def _parse_match_object(self, mo):
        """Split a match object corresponding to an accounting variable

        Returns field, mode, [account codes], [domain expression].
        """
        field, mode, account_codes, domain = mo.groups()
        if not mode:
            mode = MODE_VARIATION
        elif mode == 's':
            mode = MODE_END
        if account_codes.startswith('_'):
            account_codes = account_codes[1:]
        else:
            account_codes = account_codes[1:-1]
        if account_codes.strip():
            account_codes = [a.strip() for a in account_codes.split(',')]
        else:
            account_codes = None
        domain = domain or '[]'
        domain = tuple(safe_eval(domain))
        return field, mode, account_codes, domain

    def parse_expr(self, expr):
        """Parse an expression, extracting accounting variables.

        Domains and accounts are extracted and stored in the map
        so when all expressions have been parsed, we know what to query.
        """
        for mo in self.ACC_RE.finditer(expr):
            _, mode, account_codes, domain = self._parse_match_object(mo)
            key = (domain, mode)
            if account_codes:
                self._map_account_ids[key].update(account_codes)
            else:
                self._set_all_accounts.add(key)

    def done_parsing(self, cr, uid, account_domain, context=None):
        # load account codes and replace account codes by account ids in _map
        for key, account_codes in self._map_account_ids.items():
            self._load_account_codes(cr, uid, account_codes, account_domain,
                                     context=context)
            account_ids = set()
            for account_code in account_codes:
                account_ids.update(self._account_ids_by_code[account_code])
            self._map_account_ids[key] = list(account_ids)

    def get_aml_domain_for_expr(self, expr):
        """ Get a domain on account.move.line for an expression.

        Only accounting expression in mode 'p' and 'e' are considered.

        Prerequisite: done_parsing() must have been invoked.

        Returns a domain that can be used to search on account.move.line.
        """
        aml_domains = []
        for mo in self.ACC_RE.finditer(expr):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            if mode == MODE_INITIAL:
                continue
            aml_domain = list(domain)
            if account_codes:
                account_ids = set()
                for account_code in account_codes:
                    account_ids.update(self._account_ids_by_code[account_code])
                aml_domain.append(('account_id', 'in', tuple(account_ids)))
            if field == 'crd':
                aml_domain.append(('credit', '>', 0))
            elif field == 'deb':
                aml_domain.append(('debit', '>', 0))
            aml_domains.append(expression.normalize_domain(aml_domain))
        return expression.OR(aml_domains)

    def get_aml_domain_for_dates(self, date_start, date_end, mode):
        if mode != MODE_VARIATION:
            raise RuntimeError("")  # TODO
        return [('date', '>=', date_start), ('date', '<=', date_end)]

    def _period_has_moves(self, cr, uid, period, context=None):
        move_model = self.pool['account.move']
        return bool(move_model.search(cr, uid, [('period_id', '=', period.id)],
                                      limit=1, context=context))

    def _get_previous_opening_period(self, cr, uid, period, company_id,
                                     context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(cr, uid,
            [('date_start', '<=', period.date_start),
             ('special', '=', True),
             ('company_id', '=', company_id)],
            order="date_start desc",
            limit=1, context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_previous_normal_period(self, cr, uid, period, company_id,
                                    context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(cr, uid,
            [('date_start', '<', period.date_start),
             ('special', '=', False),
             ('company_id', '=', company_id)],
            order="date_start desc",
            limit=1,
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_first_normal_period(self, cr, uid, company_id, context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(cr, uid,
            [('special', '=', False),
             ('company_id', '=', company_id)],
            order="date_start asc",
            limit=1,
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return periods and periods[0]

    def _get_period_ids_between(self, cr, uid, period_from, period_to,
                                company_id, context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(cr, uid,
            [('date_start', '>=', period_from.date_start),
             ('date_stop', '<=', period_to.date_stop),
             ('special', '=', False),
             ('company_id', '=', company_id)],
            context=context)
        if period_from.special:
            period_ids.append(period_from.id)
        return period_ids

    def _get_period_company_ids(self, cr, uid, period_from, period_to,
                                context=None):
        period_model = self.pool['account.period']
        period_ids = period_model.search(cr, uid,
            [('date_start', '>=', period_from.date_start),
             ('date_stop', '<=', period_to.date_stop),
             ('special', '=', False)],
            context=context)
        periods = period_model.browse(cr, uid, period_ids, context=context)
        return set([p.company_id.id for p in periods])

    def _get_period_ids_for_mode(self, cr, uid, period_from, period_to, mode,
                                 context=None):
        assert not period_from.special
        assert not period_to.special
        assert period_from.company_id == period_to.company_id
        assert period_from.date_start <= period_to.date_start
        period_ids = []
        for company_id in self._get_period_company_ids(cr, uid,
                                                       period_from, period_to,
                                                       context=context):
            if mode == MODE_VARIATION:
                period_ids.extend(self._get_period_ids_between(cr, uid,
                    period_from, period_to, company_id, context=context))
            else:
                if mode == MODE_INITIAL:
                    period_to = self._get_previous_normal_period(cr, uid,
                        period_from, company_id, context=context)
                # look for opening period with moves
                opening_period = self._get_previous_opening_period(cr, uid,
                    period_from, company_id, context=context)
                if opening_period and \
                        self._period_has_moves(cr, uid, opening_period,
                                               context=context):
                    # found opening period with moves
                    if opening_period.date_start == period_from.date_start and \
                            mode == MODE_INITIAL:
                        # if the opening period has the same start date as
                        # period_from, the we'll find the initial balance
                        # in the initial period and that's it
                        period_ids.append(opening_period.id)
                        continue
                    period_from = opening_period
                else:
                    # no opening period with moves,
                    # use very first normal period
                    period_from = self._get_first_normal_period(
                        cr, uid, company_id, context=context)
                if period_to:
                    period_ids.extend(self._get_period_ids_between(
                        cr, uid, period_from, period_to, company_id,
                        context=context))
        return period_ids

    def get_aml_domain_for_periods(self, cr, uid, period_from, period_to, mode,
                                   context=None):
        period_ids = self._get_period_ids_for_mode(cr, uid,
            period_from, period_to, mode, context=context)
        return [('period_id', 'in', period_ids)]

    def do_queries(self, cr, uid, period_domain, period_domain_i,
                   period_domain_e, context=None):
        aml_model = self.pool['account.move.line']
        # {(domain, mode): {account_id: (debit, credit)}}
        self._data = defaultdict(dict)
        # fetch sum of debit/credit, grouped by account_id
        for key in self._map_account_ids:
            domain, mode = key
            if mode == MODE_VARIATION:
                domain = list(domain) + period_domain
            elif mode == MODE_INITIAL:
                domain = list(domain) + period_domain_i
            elif mode == MODE_END:
                domain = list(domain) + period_domain_e
            else:
                raise RuntimeError("unexpected mode %s" % (mode,))
            domain.append(('account_id', 'in', self._map_account_ids[key]))
            accs = aml_model.read_group(cr, uid, domain,
                                        ['debit', 'credit', 'account_id'],
                                        ['account_id'],
                                        context=context)
            for acc in accs:
                self._data[key][acc['account_id'][0]] = \
                    (acc['debit'] or 0.0, acc['credit'] or 0.0)
        # fetch sum of debit/credit for expressions with no account
        for key in self._set_all_accounts:
            domain, mode = key
            if mode == MODE_VARIATION:
                domain = list(domain) + period_domain
            elif mode == MODE_INITIAL:
                domain = list(domain) + period_domain_i
            elif mode == MODE_END:
                domain = list(domain) + period_domain_e
            else:
                raise RuntimeError("unexpected mode %s" % (mode,))
            accs = aml_model.read_group(cr, uid, domain,
                                        ['debit', 'credit'],
                                        [],
                                        context=context)
            assert len(accs) == 1
            self._data[key][None] = \
                (accs[0]['debit'] or 0.0, accs[0]['credit'] or 0.0)

    def replace_expr(self, expr):
        """Replace accounting variables in an expression by their amount.

        Returns a new expression.

        This method must be executed after do_queries().
        """
        def f(mo):
            field, mode, account_codes, domain = self._parse_match_object(mo)
            key = (domain, mode)
            account_ids_data = self._data[key]
            v = 0.0
            for account_code in account_codes or [None]:
                if account_code:
                    account_ids = self._account_ids_by_code[account_code]
                else:
                    account_ids = [None]
                for account_id in account_ids:
                    debit, credit = \
                        account_ids_data.get(account_id, (0.0, 0.0))
                    if field == 'bal':
                        v += debit - credit
                    elif field == 'deb':
                        v += debit
                    elif field == 'crd':
                        v += credit
            return '(' + repr(v) + ')'
        return self.ACC_RE.sub(f, expr)
