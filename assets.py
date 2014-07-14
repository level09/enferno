# -*- coding: utf-8 -*-
from flask.ext.assets import Bundle, Environment

css = Bundle(
    "css/bootstrap.min.css",
    "css/jasny-bootstrap.min.css",
    "css/main.css",
    filters="cssmin",
    output="public/css/common.css"
)

js = Bundle(
    "js/vendor/jquery-1.10.1.min.js",
    "js/vendor/bootstrap.min.js",
    "js/vendor/jasny-bootstrap.min.js",
    "js/main.js",
    filters='jsmin',
    output="public/js/common.js"
)

assets = Environment()

assets.register("js_all", js)
assets.register("css_all", css)