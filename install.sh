#! /bin/bash

ROOT=$(dirname $0)

cd ${ROOT}

virtualenv -p python3 venv

source venv/bin/activate

pip install -r requirements.txt
pip install -r src/odoo/requirements.txt
pip install -r src/runbot/requirements.txt

src/odoo/odoo-bin  -c runbot.conf --save \
                   -d runbot --db_port ${DBPORT} --db_host ${DBHOST} -w $DBPASSWD \
                   --addons-path=./src/odoo/addons,./src/runbot,./src/local-src \
                   --limit-memory-soft 4294967296 --limit-memory-hard 4311744512 --limit-time-real-cron=1800 \
                   -i runbot --without-demo=1 \
                   --stop-after-init
