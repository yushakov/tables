#!/bin/bash
ROOT=$(pwd)
cd node_modules/gantt-task-react/django_gantt

echo "Removing build folder..."
rm -rvf build

echo "Extracting the build archive..."
tar -xzvf build.tar.gz

echo "Copying css files.."
main_css=$(ls $ROOT/node_modules/gantt-task-react/django_gantt/build/static/css/*.css)
main_css_map=$(ls $ROOT/node_modules/gantt-task-react/django_gantt/build/static/css/*.css.map)
cp $main_css $ROOT/../static/gantt/css/main.css
cp $main_css_map $ROOT/../static/gantt/css/main.css.map

echo "Copying js files.."
main_js=$(ls $ROOT/node_modules/gantt-task-react/django_gantt/build/static/js/*.js)
main_js_map=$(ls $ROOT/node_modules/gantt-task-react/django_gantt/build/static/js/*.js.map)
cp $main_js $ROOT/../static/gantt/js/main.js
cp $main_js_map $ROOT/../static/gantt/js/main.js.map

echo "Copying manifest.."
manifest=$ROOT/node_modules/gantt-task-react/django_gantt/build/manifest.json
cp $manifest $ROOT/../static/gantt/manifest.json

cd $ROOT/../..
echo "Collect Django static files..."
python3 manage.py collectstatic