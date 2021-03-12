---
layout: default
title: People
nav_order: 1
---

# People

## Current

<div class="people-cards">
{% for person in site.people %}
<div class="person" markdown="1">
![{{ person.name }}]({{ person.image | prepend:  site.baseurl }})  
<p style='text-align:center;'><a href="{{person.link}}"><strong>{{person.name}}</strong></a></p>
{{person.content}}
</div> 
{% endfor %}
</div>

## Alumni
<div class="people-cards">
{% for person in site.alum %}
<div class="person" markdown="1">
![{{ person.name }}]({{ person.image | prepend:  site.baseurl }})  
<p style='text-align:center;'><a href="{{person.link}}"><strong>{{person.name}}</strong></a></p>
{{person.content}}
</div> 
{% endfor %}
</div>



