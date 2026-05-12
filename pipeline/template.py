TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{BUSINESS_NAME}}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--primary:{{PRIMARY_COLOR}};--primary-dark:{{PRIMARY_COLOR}};--primary-light:#eff6ff;--text:#1e293b;--muted:#64748b;--border:#e2e8f0;--white:#fff;--bg:#f8fafc}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--text);background:var(--white);line-height:1.6}
.demo-banner{background:#1e293b;color:#94a3b8;text-align:center;padding:10px 16px;font-size:12px;letter-spacing:.04em}
.demo-banner span{color:#60a5fa;font-weight:600}
nav{background:var(--white);border-bottom:1px solid var(--border);padding:0 5%;position:sticky;top:0;z-index:100}
.nav-inner{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:64px}
.nav-logo{font-size:18px;font-weight:700;color:var(--text);text-decoration:none}
.nav-cta{background:var(--primary);color:#fff;padding:9px 20px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none}
.hero{background:linear-gradient(135deg,#1e40af 0%,{{PRIMARY_COLOR}} 60%,#3b82f6 100%);padding:90px 5%;min-height:500px;display:flex;align-items:center}
.hero-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}
.hero-text{color:#fff}
.hero-badge{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);color:#bfdbfe;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:20px}
.hero h1{font-size:clamp(2rem,4vw,3rem);font-weight:700;line-height:1.15;margin-bottom:16px}
.hero-tagline{font-size:17px;color:rgba(255,255,255,.8);margin-bottom:32px;max-width:480px}
.hero-btns{display:flex;gap:12px;flex-wrap:wrap}
.btn-white{background:#fff;color:var(--primary);padding:12px 28px;border-radius:8px;font-weight:600;font-size:15px;text-decoration:none}
.btn-outline{border:2px solid rgba(255,255,255,.5);color:#fff;padding:10px 28px;border-radius:8px;font-weight:600;font-size:15px;text-decoration:none}
.hero-visual{display:flex;justify-content:center}
.hero-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:16px;padding:32px;width:100%;max-width:340px}
.hero-card-stat{margin-bottom:20px}
.hero-card-stat:last-child{margin-bottom:0}
.hero-card-num{font-size:28px;font-weight:700;color:#fff}
.hero-card-label{font-size:13px;color:rgba(255,255,255,.65);margin-top:2px}
.hero-card-bar{height:4px;background:rgba(255,255,255,.15);border-radius:2px;margin-top:8px}
.hero-card-bar-fill{height:100%;border-radius:2px;background:rgba(255,255,255,.6)}
section.about{padding:80px 5%;background:#fff}
section.services{padding:80px 5%;background:var(--bg)}
section.contact{padding:80px 5%;background:#fff}
.section-inner{max-width:1100px;margin:0 auto}
.section-tag{display:inline-block;background:var(--primary-light);color:var(--primary);padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px}
.section-title{font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;color:var(--text);margin-bottom:12px;line-height:1.2}
.section-sub{font-size:16px;color:var(--muted);max-width:560px;margin-bottom:48px}
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}
.about-text p{font-size:16px;color:var(--muted);line-height:1.8;margin-bottom:16px}
.about-visual{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.about-stat{background:var(--bg);border-radius:12px;padding:24px;text-align:center}
.about-stat-num{font-size:28px;font-weight:700;color:var(--primary)}
.about-stat-label{font-size:13px;color:var(--muted);margin-top:4px}
.services-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px}
.service-card{background:#fff;border:1px solid var(--border);border-radius:12px;padding:28px;position:relative;overflow:hidden}
.service-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--primary)}
.service-icon{width:44px;height:44px;background:var(--primary-light);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-bottom:16px;font-size:20px}
.service-name{font-size:15px;font-weight:600;color:var(--text);margin-bottom:6px}
.service-desc{font-size:13px;color:var(--muted);line-height:1.6}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start}
.contact-info{display:flex;flex-direction:column;gap:20px}
.contact-item{display:flex;align-items:flex-start;gap:14px}
.contact-icon{width:40px;height:40px;background:var(--primary-light);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px}
.contact-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.contact-value{font-size:15px;color:var(--text);margin-top:2px}
.contact-form{background:var(--bg);border-radius:16px;padding:32px}
.form-group{margin-bottom:16px}
.form-group label{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px}
.form-group input,.form-group textarea{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:8px;font-size:14px;color:var(--text);background:#fff;outline:none}
.form-group textarea{height:100px;resize:vertical}
.form-submit{width:100%;background:var(--primary);color:#fff;border:none;padding:12px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
footer{background:#1e293b;color:#94a3b8;padding:40px 5%;text-align:center}
footer .footer-name{font-size:18px;font-weight:700;color:#fff;margin-bottom:8px}
footer .footer-credit{font-size:12px;margin-top:16px;color:#64748b}
footer .footer-credit a{color:#60a5fa}
@media(max-width:768px){.hero-inner,.about-grid,.contact-grid{grid-template-columns:1fr}.hero-visual,.about-visual{display:none}}
</style>
</head>
<body>
<div class="demo-banner">This is a <span>free demo website</span> built for you by OmniCode Creations — reply to find out more</div>
<nav><div class="nav-inner"><a href="#" class="nav-logo">{{BUSINESS_NAME}}</a><a href="#contact" class="nav-cta">Get in touch</a></div></nav>
<section class="hero">
  <div class="hero-inner">
    <div class="hero-text">
      <div class="hero-badge">{{CATEGORY}}</div>
      <h1>{{BUSINESS_NAME}}</h1>
      <p class="hero-tagline">{{TAGLINE}}</p>
      <div class="hero-btns"><a href="#contact" class="btn-white">Contact us</a><a href="#services" class="btn-outline">Our services</a></div>
    </div>
    <div class="hero-visual">
      <div class="hero-card">
        <div class="hero-card-stat"><div class="hero-card-num">⭐ {{GOOGLE_RATING}}</div><div class="hero-card-label">Google rating</div><div class="hero-card-bar"><div class="hero-card-bar-fill" style="width:90%"></div></div></div>
        <div class="hero-card-stat"><div class="hero-card-num">{{GOOGLE_REVIEW_COUNT}}+</div><div class="hero-card-label">Happy customers</div><div class="hero-card-bar"><div class="hero-card-bar-fill" style="width:75%"></div></div></div>
        <div class="hero-card-stat"><div class="hero-card-num">📍 {{LOCATION}}</div><div class="hero-card-label">Based in</div></div>
      </div>
    </div>
  </div>
</section>
<section class="about">
  <div class="section-inner">
    <div class="about-grid">
      <div class="about-text">
        <div class="section-tag">About us</div>
        <h2 class="section-title">Who we are</h2>
        <p>{{DESCRIPTION}}</p>
        <p>We are proud to serve the {{LOCATION}} community with professional, reliable service you can count on.</p>
      </div>
      <div class="about-visual">
        <div class="about-stat"><div class="about-stat-num">{{GOOGLE_RATING}}★</div><div class="about-stat-label">Rating</div></div>
        <div class="about-stat"><div class="about-stat-num">{{GOOGLE_REVIEW_COUNT}}+</div><div class="about-stat-label">Reviews</div></div>
        <div class="about-stat"><div class="about-stat-num">Local</div><div class="about-stat-label">Business</div></div>
        <div class="about-stat"><div class="about-stat-num">Trusted</div><div class="about-stat-label">Service</div></div>
      </div>
    </div>
  </div>
</section>
<section class="services" id="services">
  <div class="section-inner">
    <div class="section-tag">What we offer</div>
    <h2 class="section-title">Our services</h2>
    <p class="section-sub">Everything you need, all in one place.</p>
    <div class="services-grid">
      <div class="service-card"><div class="service-icon">✦</div><div class="service-name">{{SERVICE_1}}</div><div class="service-desc">Professional service tailored to your needs.</div></div>
      <div class="service-card"><div class="service-icon">✦</div><div class="service-name">{{SERVICE_2}}</div><div class="service-desc">Professional service tailored to your needs.</div></div>
      <div class="service-card"><div class="service-icon">✦</div><div class="service-name">{{SERVICE_3}}</div><div class="service-desc">Professional service tailored to your needs.</div></div>
      <div class="service-card"><div class="service-icon">✦</div><div class="service-name">{{SERVICE_4}}</div><div class="service-desc">Professional service tailored to your needs.</div></div>
      <div class="service-card"><div class="service-icon">✦</div><div class="service-name">{{SERVICE_5}}</div><div class="service-desc">Professional service tailored to your needs.</div></div>
    </div>
  </div>
</section>
<section class="contact" id="contact">
  <div class="section-inner">
    <div class="contact-grid">
      <div>
        <div class="section-tag">Contact</div>
        <h2 class="section-title">Get in touch</h2>
        <p class="section-sub">Ready to work with us? We'd love to hear from you.</p>
        <div class="contact-info">
          <div class="contact-item"><div class="contact-icon">📍</div><div><div class="contact-label">Address</div><div class="contact-value">{{ADDRESS}}</div></div></div>
          <div class="contact-item"><div class="contact-icon">📞</div><div><div class="contact-label">Phone</div><div class="contact-value">{{PHONE}}</div></div></div>
          <div class="contact-item"><div class="contact-icon">✉️</div><div><div class="contact-label">Email</div><div class="contact-value">{{EMAIL}}</div></div></div>
        </div>
      </div>
      <div class="contact-form">
        <div class="form-group"><label>Your name</label><input type="text" placeholder="John Smith"></div>
        <div class="form-group"><label>Email address</label><input type="email" placeholder="john@example.com"></div>
        <div class="form-group"><label>Message</label><textarea placeholder="How can we help you?"></textarea></div>
        <button class="form-submit">Send message</button>
      </div>
    </div>
  </div>
</section>
<footer>
  <div class="footer-name">{{BUSINESS_NAME}}</div>
  <p>{{ADDRESS}}</p>
  <p class="footer-credit">Demo website by <a href="#">OmniCode Creations</a></p>
</footer>
</body>
</html>"""
