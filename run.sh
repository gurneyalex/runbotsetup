#!/bin/bash
ROOT=$(dirname $0)
cd ${ROOT}
export ODOO_RC=${ROOT}/runbot.conf

src/odoo/odoo-bin "$@"
