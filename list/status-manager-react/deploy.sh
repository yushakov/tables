#!/bin/bash

# nvm use 20.5.0 - run it separately

ROOT=$(pwd)
echo "Build $(pwd)..."
npm run build

echo "Copying css file.."
main_css=$(ls $ROOT/dist/assets/*.css)
cp $main_css $ROOT/../static/list/status_mgr/styles.css

echo "Copying js file.."
main_js=$(ls $ROOT/dist/assets/*.js)
cp $main_js $ROOT/../static/list/status_mgr/script.js

# echo "Making an archive..."
# tar -czvf build.tar.gz build
