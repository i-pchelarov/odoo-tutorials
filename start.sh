#!/usr/bin/env bash
source ../odoo/odoo-venv/bin/activate
../odoo/odoo-bin --addons-path=../odoo/addons,. -d rd-demo -u estate --dev xml
