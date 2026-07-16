---
layout: single
title: "Follow research updates"
permalink: /follow/
author_profile: true
---

Stay informed about new research notes, publications, projects, software releases, data resources, and presentations.

{% assign newsletter = site.data.newsletter %}
{% if newsletter.enabled and newsletter.provider == "buttondown" and newsletter.username != "YOUR_BUTTONDOWN_USERNAME" %}
<form action="https://buttondown.email/api/emails/embed-subscribe/{{ newsletter.username }}" method="post" target="popupwindow" class="follow-form">
  <label for="bd-email">Email address</label>
  <div class="follow-form__row">
    <input id="bd-email" type="email" name="email" required autocomplete="email" placeholder="name@example.com">
    <button type="submit">Subscribe</button>
  </div>
  <p class="follow-form__note">You can unsubscribe at any time. Your email is handled by the newsletter provider.</p>
</form>
{% else %}
<div class="follow-setup-panel">
  <h2>Email subscription is being configured</h2>
  <p>The site-side subscription system is ready, but automatic email delivery requires a newsletter account to be connected. Until then, you can follow updates through the RSS feed.</p>
  <p><a class="btn" href="{{ site.url }}{{ site.baseurl }}/feed.xml">Follow the RSS feed</a></p>
</div>
{% endif %}

## What subscribers will receive

- new research notes and methodological articles;
- newly added publications and conference contributions;
- project updates and analytical outputs;
- software and data-resource releases;
- selected teaching and training materials.

Messages will be limited to substantive scientific updates rather than routine site changes.
