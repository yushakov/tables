#!/bin/bash
ROOT=$(pwd)
echo "Install in $(pwd)..."
#npm install
cd node_modules/gantt-task-react
echo "Install in $(pwd)..."
# npm install
cd django_gantt
echo "Install in $(pwd)..."
# npm install
echo "Build in $(pwd)..."
npm run build

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
