---
layout: single
title: "Contact"
permalink: /contact/
author_profile: true
---

For academic collaboration, conference invitations, manuscript discussion, quantitative analysis, or applied work in marine ecology and fisheries science, you can write to me directly using the form below.

{% assign contact = site.data.contact %}
{% if contact.enabled and contact.recipient_email != "YOUR_PERSONAL_EMAIL" %}
<form class="contact-form" action="https://formsubmit.co/{{ contact.recipient_email }}" method="POST">
  <input type="hidden" name="_subject" value="New message from qselmer.github.io">
  <input type="hidden" name="_template" value="table">
  <input type="hidden" name="_captcha" value="true">
  <input type="hidden" name="_next" value="{{ site.url }}{{ contact.success_path }}">
  <input type="text" name="_honey" class="contact-form__honeypot" tabindex="-1" autocomplete="off">

  <div class="contact-form__grid">
    <div>
      <label for="contact-name">Name</label>
      <input id="contact-name" type="text" name="name" required autocomplete="name">
    </div>
    <div>
      <label for="contact-email">Email</label>
      <input id="contact-email" type="email" name="email" required autocomplete="email">
    </div>
  </div>

  <label for="contact-subject">Subject</label>
  <input id="contact-subject" type="text" name="subject" required>

  <label for="contact-topic">Reason for contact</label>
  <select id="contact-topic" name="topic">
    <option>Research collaboration</option>
    <option>Conference or symposium invitation</option>
    <option>Publication or manuscript discussion</option>
    <option>Statistical or technical consultation</option>
    <option>Teaching or training</option>
    <option>Other</option>
  </select>

  <label for="contact-message">Message</label>
  <textarea id="contact-message" name="message" rows="8" required></textarea>

  <button type="submit">Send message</button>
  <p class="contact-form__privacy">Your message will be delivered to my personal email address. Your details will only be used to respond to your enquiry.</p>
</form>
{% else %}
<div class="contact-setup-panel">
  <h2>Direct contact form</h2>
  <p>The form is technically prepared, but it cannot send messages until the personal destination email is configured. Meanwhile, you can contact me through my current professional address.</p>
  <p><a class="btn" href="mailto:oquispe@imarpe.gob.pe">Write by email</a></p>
</div>
{% endif %}

## Areas of collaboration

- quantitative marine ecology and fisheries science;
- stock assessment, population dynamics, selectivity, and recruitment;
- spatio-temporal and habitat modelling;
- environmental variability and ecosystem responses;
- multivariate indicators, thresholds, and regime shifts;
- CPUE standardization and fisheries-dependent data;
- acoustic, biological, and oceanographic information;
- reproducible workflows in R, Python, Julia, Git, and GitHub;
- scientific software, data systems, and decision-support tools;
- conference, symposium, seminar, and teaching invitations.

## Academic and professional profiles

[Google Scholar](https://scholar.google.com/citations?user=wz83egoAAAAJ) · [ORCID](https://orcid.org/0000-0001-9229-6379) · [ResearchGate](https://www.researchgate.net/profile/Elmer-Quispe-Salazar) · [GitHub](https://github.com/qselmer) · [LinkedIn](https://www.linkedin.com/in/qselmer/)
