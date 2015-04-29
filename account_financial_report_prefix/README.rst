.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3 
Financial report based on account codes prefixes
================================================

This module was written to extend the functionality of financial report model to support a new type based on account code prefix.

Currently, after having installed financial reports, there are two ways to update their definition:

* autoamtically by xml records if they are of type account_type (or account_report), too often too general
* manually otherwise providing the updated list of concerned accounts, often too painful.

This new kind of financial reports provide another way to update financial reports definitions by xml records but with a more
flexible mechanism to specify the concerned accounts than just the account type

Temporary, regarding the account.financial.report model, module is a mix of new and old APIs. The new api will be generalized
as soon as the native model of odoo account module will also be fully migrated.

Credits
=======

Contributors
------------

* Olivier Laurent (<olivier.laurent@acsone.eu>)

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.
