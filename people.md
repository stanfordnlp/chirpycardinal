---
layout: default
title: People
nav_order: 1
---

# People

## Current

{{site.collections.docs}}
<div class="people-cards">
{% assign people=site.people | sort: "order" %}
{% for person in people %}
<div class="person" markdown="1">
![{{ person.name }}]({{ person.image | prepend:  site.baseurl }})  
<p style='text-align:center;'><a href="{{person.link}}"><strong>{{person.name}}</strong></a></p>
{{person.content}}
</div> 
{% endfor %}
</div>

## Alumni
<div class="people-cards">
{% assign people=site.alum_sgc4 | sort: "order" %}
{% for person in people %}
<div class="alum">
    <p class="alum-name">
        <a href="{{person.link}}">{{person.name}}</a>
    </p>
    <p>
        {{person.content}}
    </p>
</div> 
{% endfor %}
</div>



