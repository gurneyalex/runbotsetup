How to setup runbot 13.0.5.0.0 to run your project

Prerequisites:

* postgresql
* nginx
* docker
* python3 and virtualenv

IMPORTANT:

runbot must run as system user "odoo"

This user must
* be a member of the docker group
* have createdb priviledge on the local database server

Postgresql Setup
recommended to have a separate pg cluster for hosting the odoo database of the runbot:

$ pg_createcluster -p 5444 12 runbot
$ pg_ctlcluster 12 runbot start
$ createdb -p 5444 -O odoo odoo
$ createdb -p 5444 -O odoo runbotdb

* configure the cluster to listen on a public network interface if needed
* allow access from other runbot nodes

Odoo dependencies

sudo apt install git python3-dev virtualenv python3-virtualenv gcc libsasl2-dev libldap2-dev

curl -sL https://deb.nodesource.com/setup_10.x | bash -
sudo apt install nodejs

then run

DBHOST=hostname.of.db.server DBPASSWD=odoouserpasswd DBPORT=5444  ./install.sh


Notes:

* db connection in configuration is only used for the db holding the runbot instance
* builds will use a local postgresql cluster running on the default port, and try to acces the database "postgres" (hard coded), using the user running runbot
