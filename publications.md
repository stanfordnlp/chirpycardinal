---
layout: default
title: Publications
nav_order: 2
---

# Publications

{% for pub in site.publications %}
<article class="publication-post">
{% if pub.extlink %} 
    <a href="{{ pub.extlink }}">{{ pub.title }}</a> 
{% else %} 
    <a href="{{ pub.link | prepend: site.baseurl }}">{{ pub.title }}</a>
{% endif %}<br>
<i>{{ pub.authors }}</i><br>
{{ pub.venue }}<br>
</article> 
{% endfor %}
