#! /bin/bash

ROOT=$(dirname $0)

cd ${ROOT}

virtualenv -p python3 venv

source venv/bin/activate

pip install -r requirements.txt
pip install -r src/odoo/requirements.txt
pip install -r src/runbot/requirements.txt

src/odoo/odoo-bin  -c runbot.conf --save -d runbot --db_port 5444 --addons-path=./src/odoo/addons,./src/runbot -i runbot --without-demo=1 --stop-after-init
