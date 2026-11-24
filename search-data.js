---
layout: null
permalink: /search-data.js
---
window.EVE_SEARCH=[{"url":"index.html","title":"Overview","text":"Build EVE home robot from scratch"}
{% assign guide_pages = site.pages | sort: 'url' %}
{% for item in guide_pages %}
{% if item.url contains '/docs/' or item.path == 'CONTRIBUTING.md' or item.path == 'SECURITY.md' or item.path == 'CHANGELOG.md' %}
,{"url":{{ item.url | remove_first: '/' | jsonify }},"title":{{ item.title | default: item.name | jsonify }},"text":{{ item.content | strip_html | jsonify }}}
{% endif %}
{% endfor %}
];
