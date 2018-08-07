#!/bin/sh

pip3 install -r requirements.txt

export FLASK_APP=users
export FLASK_ENV=development

flask run