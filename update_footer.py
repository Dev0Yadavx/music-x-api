with open("main.py", "r") as f:
    code = f.read()

# 1. New Glassmorphism Profile Card & Footer Styles
old_style = "/* Footer */"
new_style = """/* Developer Profile Card & Footer */
    .dev-profile-card {
      max-width: 440px;
      margin: 0 auto 20px auto;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 18px;
      backdrop-filter: blur(20px);
      box-shadow: 0 15px 35px rgba(0,0,0,0.35);
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .dev-profile-card:hover {
      border-color: var(--border-glow);
      transform: translateY(-2px);
      box-shadow: 0 20px 40px rgba(255, 42, 68, 0.25);
    }
    .dp-wrapper {
      position: relative;
      margin-bottom: 12px;
    }
    .dev-dp {
      width: 78px;
      height: 78px;
      border-radius: 50%;
      object-fit: cover;
      border: 2.5px solid transparent;
      background: linear-gradient(#07090e, #07090e) padding-box,
                  linear-gradient(135deg, #ff2a44, #ffd60a) border-box;
      box-shadow: 0 0 20px rgba(255, 42, 68, 0.45);
    }
    .verified-badge {
      position: absolute;
      bottom: 2px;
      right: 2px;
      width: 20px;
      height: 20px;
      background: #00e676;
      border: 2px solid #07090e;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #000;
    }
    .verified-badge svg {
      width: 12px;
      height: 12px;
      fill: #000;
    }
    .dev-tagline {
      font-size: 11px;
      color: var(--sub);
      font-weight: 600;
      margin-top: 3px;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    /* Footer */"""

if old_style in code and ".dev-profile-card" not in code:
    code = code.replace(old_style, new_style)

# 2. Modern Card HTML in Footer
old_footer = """    <!-- FOOTER -->
    <footer>
      <div class="footer-divider"></div>
      <div class="dev-title">DEVELOPER SECTION</div>
      <div class="dev-sig">DEV BY- —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
      
      <div class="social-links">
        <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-btn">
          <!-- Telegram SVG -->
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
          Telegram
        </a>
        <a href="https://github.com/Dev0Yadavx?tab=repositories" target="_blank" class="social-btn">
          <!-- GitHub SVG -->
          <svg viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
          GitHub
        </a>
      </div>

      <div class="copyright-txt">All copyrights © reserved —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
      <div class="made-with">Made with ❤️ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
    </footer>"""

new_footer = """    <!-- FOOTER -->
    <footer>
      <div class="footer-divider"></div>
      <div class="dev-title">DEVELOPER SECTION</div>

      <!-- Developer DP Glass Card -->
      <div class="dev-profile-card">
        <div class="dp-wrapper">
          <img src="https://avatars.githubusercontent.com/u/257059002?v=4" alt="Developer DP" class="dev-dp" loading="lazy" />
          <div class="verified-badge" title="Verified Creator">
            <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
          </div>
        </div>
        <div class="dev-sig" style="margin-bottom:2px;">DEV BY- —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
        <div class="dev-tagline">
          <span>Full Stack • API Architect</span>
        </div>
      </div>
      
      <div class="social-links">
        <a href="https://t.me/YADAVXAHIR" target="_blank" class="social-btn">
          <!-- Telegram SVG -->
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.75-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/></svg>
          Telegram
        </a>
        <a href="https://github.com/Dev0Yadavx?tab=repositories" target="_blank" class="social-btn">
          <!-- GitHub SVG -->
          <svg viewBox="0 0 24 24"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
          GitHub
        </a>
      </div>

      <div class="copyright-txt">All copyrights © reserved —͟͞͞ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
      <div class="made-with">Made with ❤️ 𝙔ᴀᴅᴀᴠ<\>x- 🇮🇳𒌋ᥫ᭡</div>
    </footer>"""

if old_footer in code:
    code = code.replace(old_footer, new_footer)

with open("main.py", "w") as f:
    f.write(code)

print("[+] Developer DP Card added successfully!")
