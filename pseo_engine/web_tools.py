"""Browser-based zero-server-cost Web Utility Studio (12 tools x KR/EN = 24 SEO pages)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pseo_engine.config import SiteConfig


@dataclass(frozen=True)
class ToolSpec:
    slug: str
    widget_id: str
    kr_title: str
    kr_h1: str
    kr_desc: str
    kr_guide: str
    kr_faqs: list[tuple[str, str]]
    en_title: str
    en_h1: str
    en_desc: str
    en_guide: str
    en_faqs: list[tuple[str, str]]
    ui_html_kr: str
    ui_html_en: str


TOOLS_JS = """
(function () {
  function copyText(text, btn) {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(function () {
      if (!btn) return;
      var old = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(function () { btn.textContent = old; }, 1200);
    });
  }

  // 1. Image Format Converter & Compressor (Canvas API)
  document.querySelectorAll('[data-widget="tool-image-convert"]').forEach(function (root) {
    var fileEl = root.querySelector('[name="file"]');
    var fmtEl = root.querySelector('[name="format"]');
    var qEl = root.querySelector('[name="quality"]');
    var btn = root.querySelector('[data-action="convert"]');
    var outEl = root.querySelector('[data-out="status"]');
    var dlEl = root.querySelector('[data-out="download"]');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var file = fileEl.files && fileEl.files[0];
      if (!file) { outEl.textContent = 'Please select an image file first.'; return; }
      var reader = new FileReader();
      reader.onload = function (ev) {
        var img = new Image();
        img.onload = function () {
          var canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          var ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          var mime = fmtEl.value || 'image/webp';
          var quality = Math.min(1, Math.max(0.1, Number(qEl.value || 0.85)));
          var dataUrl = canvas.toDataURL(mime, quality);
          var ext = mime.split('/')[1];
          var approxKb = Math.round((dataUrl.length * 3 / 4) / 1024);
          outEl.textContent = img.width + 'x' + img.height + ' -> ' + ext.toUpperCase() + ' (~' + approxKb + ' KB)';
          dlEl.href = dataUrl;
          dlEl.download = 'converted.' + ext;
          dlEl.style.display = 'inline-block';
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    });
  });

  // 2. Image Resizer
  document.querySelectorAll('[data-widget="tool-image-resize"]').forEach(function (root) {
    var fileEl = root.querySelector('[name="file"]');
    var wEl = root.querySelector('[name="width"]');
    var hEl = root.querySelector('[name="height"]');
    var btn = root.querySelector('[data-action="resize"]');
    var outEl = root.querySelector('[data-out="status"]');
    var dlEl = root.querySelector('[data-out="download"]');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var file = fileEl.files && fileEl.files[0];
      if (!file) { outEl.textContent = 'Please select an image file first.'; return; }
      var reader = new FileReader();
      reader.onload = function (ev) {
        var img = new Image();
        img.onload = function () {
          var tw = Math.max(1, Number(wEl.value || img.width));
          var th = Math.max(1, Number(hEl.value || Math.round(img.height * (tw / img.width))));
          var canvas = document.createElement('canvas');
          canvas.width = tw;
          canvas.height = th;
          canvas.getContext('2d').drawImage(img, 0, 0, tw, th);
          var dataUrl = canvas.toDataURL('image/png');
          outEl.textContent = 'Resized to ' + tw + ' x ' + th + ' px';
          dlEl.href = dataUrl;
          dlEl.download = 'resized-' + tw + 'x' + th + '.png';
          dlEl.style.display = 'inline-block';
        };
        img.src = ev.target.result;
      };
      reader.readAsDataURL(file);
    });
  });

  // 3. JSON Formatter & Validator
  document.querySelectorAll('[data-widget="tool-json"]').forEach(function (root) {
    var inp = root.querySelector('[name="input"]');
    var out = root.querySelector('[name="output"]');
    var st = root.querySelector('[data-out="status"]');
    root.querySelector('[data-action="format"]').addEventListener('click', function () {
      try {
        var obj = JSON.parse(inp.value);
        out.value = JSON.stringify(obj, null, 2);
        st.textContent = 'Valid JSON (' + out.value.length + ' chars)';
      } catch (e) { st.textContent = 'Invalid JSON: ' + e.message; }
    });
    root.querySelector('[data-action="minify"]').addEventListener('click', function () {
      try {
        out.value = JSON.stringify(JSON.parse(inp.value));
        st.textContent = 'Minified (' + out.value.length + ' chars)';
      } catch (e) { st.textContent = 'Invalid JSON: ' + e.message; }
    });
    root.querySelector('[data-action="copy"]').addEventListener('click', function (ev) {
      copyText(out.value, ev.target);
    });
  });

  // 4. JSON to CSV Converter
  document.querySelectorAll('[data-widget="tool-json-csv"]').forEach(function (root) {
    var inp = root.querySelector('[name="input"]');
    var out = root.querySelector('[name="output"]');
    var st = root.querySelector('[data-out="status"]');
    root.querySelector('[data-action="convert"]').addEventListener('click', function () {
      try {
        var arr = JSON.parse(inp.value);
        if (!Array.isArray(arr) || !arr.length) throw new Error('Input must be a non-empty JSON array.');
        var keys = Object.keys(arr[0]);
        var lines = [keys.join(',')].concat(arr.map(function (row) {
          return keys.map(function (k) {
            var v = row[k] === undefined || row[k] === null ? '' : String(row[k]);
            return '"' + v.replace(/"/g, '""') + '"';
          }).join(',');
        }));
        out.value = lines.join('\\n');
        st.textContent = 'Converted ' + arr.length + ' rows to CSV.';
      } catch (e) { st.textContent = 'Error: ' + e.message; }
    });
    root.querySelector('[data-action="copy"]').addEventListener('click', function (ev) {
      copyText(out.value, ev.target);
    });
  });

  // 5. Base64 Encode/Decode (UTF-8 safe)
  document.querySelectorAll('[data-widget="tool-base64"]').forEach(function (root) {
    var inp = root.querySelector('[name="input"]');
    var out = root.querySelector('[name="output"]');
    var st = root.querySelector('[data-out="status"]');
    root.querySelector('[data-action="encode"]').addEventListener('click', function () {
      try {
        var bytes = new TextEncoder().encode(inp.value);
        var bin = '';
        bytes.forEach(function (b) { bin += String.fromCharCode(b); });
        out.value = btoa(bin);
        st.textContent = 'Encoded (' + out.value.length + ' chars)';
      } catch (e) { st.textContent = 'Error: ' + e.message; }
    });
    root.querySelector('[data-action="decode"]').addEventListener('click', function () {
      try {
        var bin = atob(inp.value.trim());
        var bytes = Uint8Array.from(bin, function (c) { return c.charCodeAt(0); });
        out.value = new TextDecoder().decode(bytes);
        st.textContent = 'Decoded (' + out.value.length + ' chars)';
      } catch (e) { st.textContent = 'Error: ' + e.message; }
    });
  });

  // 6. JWT Decoder
  document.querySelectorAll('[data-widget="tool-jwt"]').forEach(function (root) {
    var inp = root.querySelector('[name="input"]');
    var out = root.querySelector('[name="output"]');
    var st = root.querySelector('[data-out="status"]');
    function decodePart(seg) {
      var b64 = seg.replace(/-/g, '+').replace(/_/g, '/');
      while (b64.length % 4) b64 += '=';
      return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(b64), function (c) { return c.charCodeAt(0); })));
    }
    root.querySelector('[data-action="decode"]').addEventListener('click', function () {
      try {
        var parts = inp.value.trim().split('.');
        if (parts.length < 2) throw new Error('Invalid JWT format (expected header.payload.signature).');
        var header = decodePart(parts[0]);
        var payload = decodePart(parts[1]);
        out.value = JSON.stringify({ header: header, payload: payload }, null, 2);
        st.textContent = payload.exp ? ('exp: ' + new Date(payload.exp * 1000).toISOString()) : 'Decoded successfully';
      } catch (e) { st.textContent = 'Error: ' + e.message; }
    });
  });

  // 7. Text Diff Checker
  document.querySelectorAll('[data-widget="tool-diff"]').forEach(function (root) {
    var aEl = root.querySelector('[name="left"]');
    var bEl = root.querySelector('[name="right"]');
    var out = root.querySelector('[data-out="diff"]');
    root.querySelector('[data-action="compare"]').addEventListener('click', function () {
      var a = aEl.value.split('\\n');
      var b = bEl.value.split('\\n');
      var maxLen = Math.max(a.length, b.length);
      var rows = [];
      for (var i = 0; i < maxLen; i++) {
        var la = a[i] === undefined ? '' : a[i];
        var lb = b[i] === undefined ? '' : b[i];
        if (la === lb) rows.push('  ' + la);
        else {
          if (a[i] !== undefined) rows.push('- ' + la);
          if (b[i] !== undefined) rows.push('+ ' + lb);
        }
      }
      out.textContent = rows.join('\\n');
    });
  });

  // 8. Text Cleaner & Counter
  document.querySelectorAll('[data-widget="tool-text-clean"]').forEach(function (root) {
    var inp = root.querySelector('[name="input"]');
    var out = root.querySelector('[name="output"]');
    var st = root.querySelector('[data-out="status"]');
    function stats(txt) {
      var bytes = new TextEncoder().encode(txt).length;
      var lines = txt ? txt.split('\\n').length : 0;
      st.textContent = txt.length + ' chars | ' + txt.replace(/\\s/g, '').length + ' no-space | ' + bytes + ' bytes | ' + lines + ' lines';
    }
    inp.addEventListener('input', function () { stats(inp.value); });
    root.querySelector('[data-action="dedupe"]').addEventListener('click', function () {
      var seen = {};
      var res = inp.value.split('\\n').filter(function (l) {
        if (seen[l]) return false;
        seen[l] = true;
        return true;
      }).join('\\n');
      out.value = res;
      stats(res);
    });
    root.querySelector('[data-action="sort"]').addEventListener('click', function () {
      var res = inp.value.split('\\n').sort().join('\\n');
      out.value = res;
      stats(res);
    });
    stats(inp.value);
  });

  // 9. Password & UUID Generator
  document.querySelectorAll('[data-widget="tool-password"]').forEach(function (root) {
    var lenEl = root.querySelector('[name="length"]');
    var out = root.querySelector('[name="output"]');
    var uuidOut = root.querySelector('[data-out="uuid"]');
    function gen() {
      var len = Math.min(64, Math.max(8, Number(lenEl.value || 16)));
      var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*_-';
      var arr = new Uint32Array(len);
      crypto.getRandomValues(arr);
      var pw = '';
      for (var i = 0; i < len; i++) pw += chars[arr[i] % chars.length];
      out.value = pw;
      uuidOut.textContent = (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx');
    }
    root.querySelector('[data-action="generate"]').addEventListener('click', gen);
    root.querySelector('[data-action="copy"]').addEventListener('click', function (ev) { copyText(out.value, ev.target); });
    gen();
  });

  // 10. UTM Builder & URL Encoder
  document.querySelectorAll('[data-widget="tool-utm"]').forEach(function (root) {
    var base = root.querySelector('[name="url"]');
    var src = root.querySelector('[name="source"]');
    var med = root.querySelector('[name="medium"]');
    var camp = root.querySelector('[name="campaign"]');
    var out = root.querySelector('[name="output"]');
    function build() {
      var u = (base.value || '').trim();
      if (!u) { out.value = ''; return; }
      var params = new URLSearchParams();
      if (src.value) params.set('utm_source', src.value.trim());
      if (med.value) params.set('utm_medium', med.value.trim());
      if (camp.value) params.set('utm_campaign', camp.value.trim());
      var sep = u.indexOf('?') >= 0 ? '&' : '?';
      out.value = params.toString() ? (u + sep + params.toString()) : u;
    }
    [base, src, med, camp].forEach(function (el) { el.addEventListener('input', build); });
    root.querySelector('[data-action="copy"]').addEventListener('click', function (ev) { copyText(out.value, ev.target); });
    build();
  });

  // 11. SEO Meta Tag Generator
  document.querySelectorAll('[data-widget="tool-seo-meta"]').forEach(function (root) {
    var tEl = root.querySelector('[name="title"]');
    var dEl = root.querySelector('[name="desc"]');
    var uEl = root.querySelector('[name="url"]');
    var out = root.querySelector('[name="output"]');
    function build() {
      var t = tEl.value || '';
      var d = dEl.value || '';
      var u = uEl.value || '';
      out.value =
        '<title>' + t + '</title>\\n' +
        '<meta name="description" content="' + d + '">\\n' +
        '<link rel="canonical" href="' + u + '">\\n' +
        '<meta property="og:title" content="' + t + '">\\n' +
        '<meta property="og:description" content="' + d + '">\\n' +
        '<meta property="og:url" content="' + u + '">';
    }
    [tEl, dEl, uEl].forEach(function (el) { el.addEventListener('input', build); });
    root.querySelector('[data-action="copy"]').addEventListener('click', function (ev) { copyText(out.value, ev.target); });
    build();
  });

  // 12. Color HEX <-> RGB Converter
  document.querySelectorAll('[data-widget="tool-color"]').forEach(function (root) {
    var hexEl = root.querySelector('[name="hex"]');
    var rgbOut = root.querySelector('[data-out="rgb"]');
    var hslOut = root.querySelector('[data-out="hsl"]');
    var swatch = root.querySelector('[data-out="swatch"]');
    function update() {
      var h = (hexEl.value || '#2563eb').trim().replace('#', '');
      if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
      if (!/^[0-9a-fA-F]{6}$/.test(h)) return;
      var r = parseInt(h.slice(0, 2), 16);
      var g = parseInt(h.slice(2, 4), 16);
      var b = parseInt(h.slice(4, 6), 16);
      rgbOut.textContent = 'rgb(' + r + ', ' + g + ', ' + b + ')';
      var rn = r / 255, gn = g / 255, bn = b / 255;
      var max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn);
      var l = (max + min) / 2, s = 0, hue = 0;
      if (max !== min) {
        var d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === rn) hue = (gn - bn) / d + (gn < bn ? 6 : 0);
        else if (max === gn) hue = (bn - rn) / d + 2;
        else hue = (rn - gn) / d + 4;
        hue = Math.round(hue * 60);
      }
      hslOut.textContent = 'hsl(' + hue + ', ' + Math.round(s * 100) + '%, ' + Math.round(l * 100) + '%)';
      swatch.style.background = '#' + h;
    }
    hexEl.addEventListener('input', update);
    update();
  });
})();
"""


def _tool_specs() -> list[ToolSpec]:
    return [
        ToolSpec(
            slug="image-converter",
            widget_id="tool-image-convert",
            kr_title="무료 이미지 포맷 변환기 & 용량 압축 (WebP · PNG · JPG)",
            kr_h1="브라우저 무료 이미지 변환 · 용량 압축기 (WebP / PNG / JPG)",
            kr_desc="서버 업로드 없이 브라우저에서 즉시 WebP, PNG, JPG 이미지를 변환하고 용량을 압축하세요. 100% 무료·개인정보 안전.",
            kr_guide="이 도구는 HTML5 Canvas API를 사용해 사용자의 PC·스마트폰 브라우저 내부에서만 이미지를 변환합니다. 사진 파일이 외부 서버로 전송되지 않아 신분증·문서 이미지도 안심하고 WebP·JPG·PNG로 변환 및 용량 최적화를 진행할 수 있습니다. 블로그·쇼핑몰 로딩 속도를 높이려면 WebP(품질 0.80~0.85) 변환을 권장합니다.",
            kr_faqs=[("이미지가 서버에 저장되나요?", "아니요. 모든 변환은 브라우저 메모리에서만 처리되며 서버로 전혀 전송되지 않습니다."), ("WebP로 변환하면 얼마나 가벼워지나요?", "동일 화질 기준 PNG/JPG 대비 보통 25%~60% 이상 파일 용량이 줄어듭니다.")],
            en_title="Free Online Image Converter & Compressor (WebP, PNG, JPG)",
            en_h1="Private Browser Image Converter & Compressor (WebP / PNG / JPG)",
            en_desc="Convert and compress PNG, JPG, and WebP images directly in your browser with zero server uploads. Fast, free, and 100% private.",
            en_guide="Convert images between WebP, JPEG, and PNG locally using your browser's native Canvas API. Because no files leave your device, sensitive screenshots and assets remain completely private while achieving up to 60% file size reduction for faster web performance.",
            en_faqs=[("Are my images uploaded to a server?", "No. Everything runs 100% client-side in your browser."), ("Which format is best for web SEO?", "WebP at 0.80-0.85 quality delivers the best balance of visual clarity and Core Web Vitals speed.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>이미지 선택</label><input type="file" name="file" accept="image/*"></div><div class="field"><label>변환 포맷</label><select name="format"><option value="image/webp">WebP (추천)</option><option value="image/jpeg">JPG</option><option value="image/png">PNG</option></select></div><div class="field"><label>압축 품질 (0.1~1.0)</label><input type="number" name="quality" value="0.85" step="0.05" min="0.1" max="1"></div></div><div style="margin-top:14px;"><button class="btn-cta" type="button" data-action="convert">즉시 변환하기</button> <a class="btn-cta" data-out="download" style="display:none;background:#2563eb;">변환 파일 다운로드</a></div><p data-out="status" style="margin-top:10px;font-weight:700;"></p>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Select Image</label><input type="file" name="file" accept="image/*"></div><div class="field"><label>Output Format</label><select name="format"><option value="image/webp">WebP (Recommended)</option><option value="image/jpeg">JPEG</option><option value="image/png">PNG</option></select></div><div class="field"><label>Quality (0.1 - 1.0)</label><input type="number" name="quality" value="0.85" step="0.05" min="0.1" max="1"></div></div><div style="margin-top:14px;"><button class="btn-cta" type="button" data-action="convert">Convert Now</button> <a class="btn-cta" data-out="download" style="display:none;background:#2563eb;">Download Converted Image</a></div><p data-out="status" style="margin-top:10px;font-weight:700;"></p>""",
        ),
        ToolSpec(
            slug="image-resizer",
            widget_id="tool-image-resize",
            kr_title="무료 이미지 크기 조절기 (픽셀 리사이즈 · 비율 자동)",
            kr_h1="온라인 무료 이미지 리사이저 (가로·세로 픽셀 조절)",
            kr_desc="별도 프로그램 설치 없이 브라우저에서 즉시 이미지 가로·세로 픽셀 크기를 조절하고 PNG로 저장하세요.",
            kr_guide="블로그 썸네일(1200x630), 스마트스토어 대표이미지(1000x1000), 인스타그램 정사각형(1080x1080) 규격에 맞춰 브라우저에서 즉시 이미지 크기를 조절할 수 있습니다. 가로 폭만 입력하고 세로를 비워두면 원본 비율이 자동 유지됩니다.",
            kr_faqs=[("원본 비율을 유지하려면 어떻게 하나요?", "가로(px) 값만 입력하고 세로 칸을 비워두시면 비율에 맞춰 자동 계산됩니다."), ("화질 저하 없이 줄일 수 있나요?", "PNG 무손실 포맷으로 출력되어 텍스트·캡처 이미지도 선명하게 유지됩니다.")],
            en_title="Free Online Image Resizer (Exact Pixel Dimensions)",
            en_h1="Instant Browser Image Resizer (No Upload Required)",
            en_desc="Resize PNG, JPG, and WebP images to exact pixel dimensions directly in your browser. Automatic aspect ratio support.",
            en_guide="Resize product photos, Open Graph thumbnails (1200x630), and social media assets instantly without uploading files to third-party servers. Leave height blank to preserve the original aspect ratio automatically.",
            en_faqs=[("How do I keep the aspect ratio?", "Enter only the target width and leave the height input empty."), ("Is there a file size limit?", "No server limits apply because resizing runs locally on your device.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>이미지 선택</label><input type="file" name="file" accept="image/*"></div><div class="field"><label>가로 (px)</label><input type="number" name="width" value="1200"></div><div class="field"><label>세로 (px, 비우면 자동)</label><input type="number" name="height" placeholder="자동 비율"></div></div><div style="margin-top:14px;"><button class="btn-cta" type="button" data-action="resize">크기 조절하기</button> <a class="btn-cta" data-out="download" style="display:none;background:#2563eb;">다운로드</a></div><p data-out="status" style="margin-top:10px;font-weight:700;"></p>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Select Image</label><input type="file" name="file" accept="image/*"></div><div class="field"><label>Width (px)</label><input type="number" name="width" value="1200"></div><div class="field"><label>Height (px, optional)</label><input type="number" name="height" placeholder="Auto ratio"></div></div><div style="margin-top:14px;"><button class="btn-cta" type="button" data-action="resize">Resize Image</button> <a class="btn-cta" data-out="download" style="display:none;background:#2563eb;">Download PNG</a></div><p data-out="status" style="margin-top:10px;font-weight:700;"></p>""",
        ),
        ToolSpec(
            slug="json-formatter",
            widget_id="tool-json",
            kr_title="JSON 포매터 · 문법 검증기 · 압축(Minify) 온라인 도구",
            kr_h1="JSON 포매터 · 정렬 · 문법 검사기 (브라우저 로컬 처리)",
            kr_desc="API 응답 JSON을 보기 좋게 2칸 들여쓰기로 정렬하고 문법 오류를 즉시 검출합니다. 서버 전송 없어 민감한 API 데이터도 안전합니다.",
            kr_guide="복잡한 REST API 응답이나 설정 파일(JSON)의 쉼표 누락·따옴표 오류를 즉시 검증하고 가독성 높게 정렬(Beautify)하거나 한 줄로 압축(Minify)합니다. 모든 파싱은 로컬 브라우저에서 수행됩니다.",
            kr_faqs=[("JSON 문법 오류 원인을 알 수 있나요?", "유효하지 않은 JSON 입력 시 정확한 파싱 오류 메시지가 하단에 표시됩니다."), ("대용량 JSON도 안전한가요?", "네트워크 전송 없이 브라우저 메모리에서 즉시 처리됩니다.")],
            en_title="JSON Formatter, Validator & Minifier Online (100% Private)",
            en_h1="JSON Formatter, Validator & Minifier",
            en_desc="Beautify, validate, and minify JSON payloads instantly inside your browser with zero server logging.",
            en_guide="Format messy API responses into clean 2-space indented JSON, detect syntax errors immediately, or minify JSON for production configs—all locally without transmitting sensitive tokens or payloads.",
            en_faqs=[("Does this tool log my JSON?", "Never. All parsing happens locally via JavaScript JSON.parse."), ("Can I minify formatted JSON?", "Yes, click Minify to strip all whitespace into a compact single line.")],
            ui_html_kr="""<div class="field"><label>JSON 입력</label><textarea name="input" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">{"service":"moneypinlab","status":"ok","items":[1,2,3]}</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="format">정렬 (Format)</button> <button class="btn-cta" type="button" data-action="minify" style="background:#334155;">압축 (Minify)</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">복사</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>결과</label><textarea name="output" rows="6" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
            ui_html_en="""<div class="field"><label>Input JSON</label><textarea name="input" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">{"service":"moneypinlab","status":"ok","items":[1,2,3]}</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="format">Format</button> <button class="btn-cta" type="button" data-action="minify" style="background:#334155;">Minify</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">Copy</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>Output</label><textarea name="output" rows="6" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
        ),
        ToolSpec(
            slug="json-to-csv",
            widget_id="tool-json-csv",
            kr_title="JSON → CSV 변환기 (엑셀 · 구글시트용 즉시 변환)",
            kr_h1="무료 JSON to CSV 변환기 (엑셀 호환)",
            kr_desc="JSON 배열 데이터를 엑셀·구글 스프레드시트에서 바로 열 수 있는 CSV 형식으로 1초 만에 변환합니다.",
            kr_guide="공공데이터 API나 DB에서 추출한 JSON 객체 배열을 쉼표 구분(CSV) 표 형식으로 변환합니다. 쉼표·따옴표가 포함된 문자열도 RFC 표준에 맞게 안전하게 이스케이프 처리됩니다.",
            kr_faqs=[("어떤 형식의 JSON을 넣어야 하나요?", "[{\"name\":\"A\",\"price\":1000}] 형태의 객체 배열(Array of Objects)을 입력하세요."), ("엑셀에서 한글이 깨지지 않나요?", "복사 후 구글 시트나 UTF-8 CSV로 저장하면 한글이 완벽히 유지됩니다.")],
            en_title="JSON to CSV Converter Online (Excel & Google Sheets Ready)",
            en_h1="Instant JSON to CSV Converter",
            en_desc="Convert JSON arrays into clean, RFC-compliant CSV tables ready for Excel and Google Sheets directly in your browser.",
            en_guide="Transform API JSON arrays into spreadsheet-ready CSV output with proper double-quote escaping, running 100% locally in your browser.",
            en_faqs=[("What JSON structure is supported?", "A top-level JSON array of flat objects (e.g., [{\"id\":1,\"name\":\"Item\"}])."), ("Is my dataset sent to any server?", "No, conversion is executed purely in local JavaScript.")],
            ui_html_kr="""<div class="field"><label>JSON 배열 입력</label><textarea name="input" rows="5" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">[{"bank":"KB","rate":3.25},{"bank":"Shinhan","rate":3.20}]</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="convert">CSV로 변환</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">복사</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>CSV 결과</label><textarea name="output" rows="5" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
            ui_html_en="""<div class="field"><label>JSON Array Input</label><textarea name="input" rows="5" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">[{"product":"Savings","apr":4.5},{"product":"CD","apr":4.8}]</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="convert">Convert to CSV</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">Copy CSV</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>CSV Output</label><textarea name="output" rows="5" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
        ),
        ToolSpec(
            slug="base64-encoder",
            widget_id="tool-base64",
            kr_title="Base64 인코더 · 디코더 (UTF-8 한글 완벽 지원)",
            kr_h1="Base64 인코딩 · 디코딩 도구 (UTF-8 한글 지원)",
            kr_desc="한글과 특수문자가 깨지지 않는 UTF-8 기반 Base64 인코더·디코더입니다. API 헤더·인증 문자열 변환에 활용하세요.",
            kr_guide="웹 개발과 API 인증(Basic Auth)에서 자주 사용하는 Base64 인코딩·디코딩을 TextEncoder/TextDecoder 기반으로 한글 깨짐 없이 정확하게 처리합니다.",
            kr_faqs=[("한글을 Base64로 인코딩해도 안 깨지나요?", "네, UTF-8 바이트 변환 후 Base64를 적용해 한글·이모지도 완벽히 복원됩니다."), ("입력한 인증키가 저장되나요?", "아니요. 로컬 브라우저에서만 계산됩니다.")],
            en_title="Base64 Encoder & Decoder Online (UTF-8 Safe)",
            en_h1="UTF-8 Safe Base64 Encoder & Decoder",
            en_desc="Encode or decode Base64 strings with full Unicode/UTF-8 support directly in your browser.",
            en_guide="Quickly encode credentials, configuration strings, or Unicode text to Base64 and decode Base64 back to plain text using standard UTF-8 encoding locally.",
            en_faqs=[("Does it support Unicode and emojis?", "Yes, it uses standard TextEncoder/TextDecoder UTF-8 handling."), ("Is it safe for API tokens?", "Yes, zero data leaves your browser tab.")],
            ui_html_kr="""<div class="field"><label>입력 텍스트</label><textarea name="input" rows="4" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">안녕하세요 Base64 테스트</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="encode">인코딩 (Encode)</button> <button class="btn-cta" type="button" data-action="decode" style="background:#2563eb;">디코딩 (Decode)</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>결과</label><textarea name="output" rows="4" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
            ui_html_en="""<div class="field"><label>Input Text</label><textarea name="input" rows="4" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">Hello Base64 World</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="encode">Encode</button> <button class="btn-cta" type="button" data-action="decode" style="background:#2563eb;">Decode</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>Result</label><textarea name="output" rows="4" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
        ),
        ToolSpec(
            slug="jwt-decoder",
            widget_id="tool-jwt",
            kr_title="JWT 디코더 (JSON Web Token 헤더·페이로드·만료시간 확인)",
            kr_h1="안전한 로컬 JWT 디코더 (Header / Payload 분석)",
            kr_desc="JWT 토큰을 서버로 보내지 않고 브라우저에서 즉시 Header, Payload, 만료 시각(exp)을 디코딩합니다.",
            kr_guide="OAuth2, OpenID Connect, REST API 디버깅 시 JWT 토큰의 클레임(sub, iat, exp, role 등)을 안전하게 확인하세요. 모든 디코딩은 브라우저 내부에서만 수행됩니다.",
            kr_faqs=[("JWT 서명 검증도 하나요?", "브라우저 로컬 디코더는 Header와 Payload 구조를 즉시 확인하는 용도이며 비밀키는 입력받지 않습니다."), ("토큰이 외부로 유출될 위험은 없나요?", "네트워크 요청을 전혀 보내지 않으므로 안전합니다.")],
            en_title="JWT Decoder Online — Inspect Header, Payload & Expiration Locally",
            en_h1="Client-Side JWT (JSON Web Token) Decoder",
            en_desc="Decode JWT headers, claims, and exp timestamps safely in your browser without sending tokens to any server.",
            en_guide="Debug authentication flows safely by inspecting JWT headers, payloads, and ISO expiration timestamps completely offline in your browser.",
            en_faqs=[("Are my JWT tokens transmitted?", "No. Decoding uses local Base64URL parsing with zero server calls."), ("Can I check token expiration?", "Yes, if an exp claim is present it is automatically formatted as an ISO timestamp.")],
            ui_html_kr="""<div class="field"><label>JWT 토큰 입력</label><textarea name="input" rows="3" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik1vbmV5UGluTGFiIiwiZXhwIjoxODkzNDU2MDAwfQ.signature</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="decode">JWT 디코딩</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>디코딩 결과 (JSON)</label><textarea name="output" rows="7" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
            ui_html_en="""<div class="field"><label>JWT Token</label><textarea name="input" rows="3" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik1vbmV5UGluTGFiIiwiZXhwIjoxODkzNDU2MDAwfQ.signature</textarea></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="decode">Decode JWT</button></div><p data-out="status" style="font-weight:700;"></p><div class="field"><label>Decoded Header &amp; Payload</label><textarea name="output" rows="7" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
        ),
        ToolSpec(
            slug="text-diff",
            widget_id="tool-diff",
            kr_title="온라인 텍스트 비교기 (문서·코드 차이점 Diff 확인)",
            kr_h1="무료 온라인 텍스트 비교기 (Text Diff Checker)",
            kr_desc="두 문서나 계약서, 코드의 변경된 줄(- 삭제 / + 추가)을 브라우저에서 즉시 비교해 드립니다.",
            kr_guide="계약서 수정본, 블로그 원고, 소스코드 두 버전을 나란히 붙여넣고 어떤 줄이 바뀌었는지 한눈에 확인하세요. 문서 내용이 외부 서버로 전송되지 않아 보안 문서도 안심하고 비교할 수 있습니다.",
            kr_faqs=[("한글 계약서나 보고서도 비교할 수 있나요?", "네, 줄 단위로 모든 한글·영문 문서의 변경점을 즉시 비교합니다."), ("문서가 저장되나요?", "아니요. 새로고침하면 브라우저 메모리에서 즉시 사라집니다.")],
            en_title="Online Text Diff Checker — Compare Two Documents Privately",
            en_h1="Free Online Text & Code Diff Checker",
            en_desc="Compare two blocks of text or code line-by-line directly in your browser to spot additions and deletions instantly.",
            en_guide="Paste original and revised text side-by-side to highlight line-level differences (- removed, + added) without uploading confidential drafts to any server.",
            en_faqs=[("Is my text stored anywhere?", "No. Comparison runs purely in client-side JavaScript."), ("Does it work for code and prose?", "Yes, any plain text, JSON, YAML, or contract draft works instantly.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>원본 텍스트</label><textarea name="left" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">첫 번째 줄\n기존 조건 3.1%\n세 번째 줄</textarea></div><div class="field"><label>수정본 텍스트</label><textarea name="right" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">첫 번째 줄\n변경 조건 3.5%\n세 번째 줄</textarea></div></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="compare">차이점 비교하기</button></div><pre data-out="diff" style="background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px;overflow-x:auto;"></pre>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Original Text</label><textarea name="left" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">Line 1\nOld price: $19\nLine 3</textarea></div><div class="field"><label>Modified Text</label><textarea name="right" rows="6" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">Line 1\nNew price: $24\nLine 3</textarea></div></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="compare">Compare Text</button></div><pre data-out="diff" style="background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px;overflow-x:auto;"></pre>""",
        ),
        ToolSpec(
            slug="text-cleaner",
            widget_id="tool-text-clean",
            kr_title="글자수 세기 · 바이트 계산 · 중복 줄 제거 · 정렬 도구",
            kr_h1="글자수/바이트 카운터 · 중복 줄 제거 · 가나다 정렬기",
            kr_desc="자기소개서 글자수·공백제외·바이트 수 실시간 확인 및 키워드 목록 중복 제거·자동 정렬을 한 번에 처리하세요.",
            kr_guide="취업 자기소개서, 블로그 SEO 원고, 마케팅 키워드 리스트를 정리할 때 공백 포함/제외 글자수와 UTF-8 바이트 수를 실시간으로 확인하고, 중복된 줄을 클릭 한 번에 제거할 수 있습니다.",
            kr_faqs=[("공백 제외 글자수와 바이트 수가 동시에 나오나요?", "네, 입력과 동시에 글자수, 공백제외, 바이트, 줄 수가 실시간 표시됩니다."), ("키워드 중복 제거도 되나요?", "한 줄에 하나씩 키워드를 넣고 '중복 줄 제거'를 누르면 중복이 즉시 정리됩니다.")],
            en_title="Word & Character Counter, Duplicate Line Remover & Sorter",
            en_h1="Text Cleaner, Character/Byte Counter & Duplicate Remover",
            en_desc="Count characters, bytes, and lines in real time, remove duplicate lines, and sort lists alphabetically in one click.",
            en_guide="Clean up keyword lists, essays, and CSV columns instantly with live character/byte counts, one-click deduplication, and alphabetical sorting.",
            en_faqs=[("Does deduplication preserve order?", "Yes, the first occurrence of each line is preserved in original order."), ("How are bytes calculated?", "Using standard UTF-8 byte encoding via TextEncoder.")],
            ui_html_kr="""<div class="field"><label>텍스트 입력</label><textarea name="input" rows="5" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">키워드A\n키워드B\n키워드A\n키워드C</textarea></div><p data-out="status" style="font-weight:700;margin:10px 0;"></p><div style="margin-bottom:12px;"><button class="btn-cta" type="button" data-action="dedupe">중복 줄 제거</button> <button class="btn-cta" type="button" data-action="sort" style="background:#2563eb;">가나다/ABC 정렬</button></div><div class="field"><label>정리 결과</label><textarea name="output" rows="5" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
            ui_html_en="""<div class="field"><label>Input Text</label><textarea name="input" rows="5" style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;">banana\napple\nbanana\ncherry</textarea></div><p data-out="status" style="font-weight:700;margin:10px 0;"></p><div style="margin-bottom:12px;"><button class="btn-cta" type="button" data-action="dedupe">Remove Duplicates</button> <button class="btn-cta" type="button" data-action="sort" style="background:#2563eb;">Sort A-Z</button></div><div class="field"><label>Cleaned Output</label><textarea name="output" rows="5" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div>""",
        ),
        ToolSpec(
            slug="password-generator",
            widget_id="tool-password",
            kr_title="안전한 랜덤 비밀번호 생성기 & UUID v4 발급기",
            kr_h1="암호학적 안전 비밀번호 · UUID v4 생성기",
            kr_desc="브라우저 Web Crypto API로 해킹에 강한 랜덤 비밀번호와 개발용 UUID v4를 즉시 생성하세요.",
            kr_guide="일반 Math.random()이 아닌 브라우저 내장 암호학적 난수 생성기(crypto.getRandomValues)를 사용해 예측 불가능한 고강도 비밀번호와 표준 UUID v4를 생성합니다.",
            kr_faqs=[("생성된 비밀번호가 서버에 기록되나요?", "아니요. 오직 사용자 기기의 Web Crypto API로만 생성되며 저장되지 않습니다."), ("권장 비밀번호 길이는 얼마인가요?", "중요 금융·업무 계정은 16자리 이상 대소문자·숫자·특수문자 조합을 권장합니다.")],
            en_title="Secure Random Password & UUID v4 Generator (Web Crypto)",
            en_h1="Cryptographically Secure Password & UUID v4 Generator",
            en_desc="Generate unguessable passwords and standard UUID v4 identifiers locally using the browser Web Crypto API.",
            en_guide="Uses window.crypto.getRandomValues for true cryptographic randomness directly on your device—never logged or transmitted.",
            en_faqs=[("Is this safer than Math.random()?", "Yes, Web Crypto API provides cryptographically strong random values."), ("Can I generate UUID v4 too?", "Yes, a fresh RFC 4122 UUID v4 is generated alongside every password.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>비밀번호 길이 (8~64)</label><input type="number" name="length" value="18" min="8" max="64"></div><div class="field"><label>생성된 비밀번호</label><input type="text" name="output" readonly></div></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="generate">새로 생성</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">비밀번호 복사</button></div><p><strong>UUID v4:</strong> <code data-out="uuid"></code></p>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Password Length (8-64)</label><input type="number" name="length" value="18" min="8" max="64"></div><div class="field"><label>Generated Password</label><input type="text" name="output" readonly></div></div><div style="margin:12px 0;"><button class="btn-cta" type="button" data-action="generate">Generate New</button> <button class="btn-cta" type="button" data-action="copy" style="background:#2563eb;">Copy Password</button></div><p><strong>UUID v4:</strong> <code data-out="uuid"></code></p>""",
        ),
        ToolSpec(
            slug="utm-builder",
            widget_id="tool-utm",
            kr_title="GA4 UTM 파라미터 링크 생성기 (마케팅 추적 URL 빌더)",
            kr_h1="무료 GA4 UTM 링크 빌더 (광고·SNS 유입 추적)",
            kr_desc="구글 애널리틱스(GA4)에서 네이버·당근·인스타·유튜브 유입 성과를 정확히 측정하는 UTM 추적 링크를 3초 만에 만드세요.",
            kr_guide="퍼포먼스 마케팅에서 매체별 클릭·전환 성과를 정확히 구분하려면 utm_source, utm_medium, utm_campaign 파라미터가 필수입니다. 입력과 동시에 URL 인코딩까지 자동 처리된 추적 링크가 생성됩니다.",
            kr_faqs=[("utm_source와 utm_medium 차이는 무엇인가요?", "source는 유입 출처(naver, karrot, youtube), medium은 매체 유형(cpc, social, email)을 의미합니다."), ("기존에 쿼리 파라미터가 있는 URL에도 쓸 수 있나요?", "네, URL에 '?'가 이미 있으면 자동으로 '&'로 이어 붙여 줍니다.")],
            en_title="Free GA4 UTM Link Builder — Campaign URL Generator",
            en_h1="GA4 Campaign UTM URL Builder",
            en_desc="Create properly encoded UTM tracking URLs for Google Analytics 4, paid ads, newsletters, and social media campaigns.",
            en_guide="Standardize your marketing attribution by generating clean utm_source, utm_medium, and utm_campaign tracking links in seconds.",
            en_faqs=[("Does this work with existing query strings?", "Yes, it automatically detects '?' and appends parameters with '&'."), ("Are UTM values case-sensitive in GA4?", "Yes, always stick to lowercase values like cpc, email, and google.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>랜딩 페이지 URL</label><input type="url" name="url" value="https://example.com/promo"></div><div class="field"><label>utm_source (매체)</label><input type="text" name="source" value="karrot"></div><div class="field"><label>utm_medium (유형)</label><input type="text" name="medium" value="cpc"></div><div class="field"><label>utm_campaign (캠페인)</label><input type="text" name="campaign" value="spring_2026"></div></div><div class="field" style="margin-top:12px;"><label>생성된 UTM 추적 링크</label><input type="text" name="output" readonly></div><div style="margin-top:12px;"><button class="btn-cta" type="button" data-action="copy">추적 링크 복사</button></div>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Landing Page URL</label><input type="url" name="url" value="https://example.com/offer"></div><div class="field"><label>utm_source</label><input type="text" name="source" value="google"></div><div class="field"><label>utm_medium</label><input type="text" name="medium" value="cpc"></div><div class="field"><label>utm_campaign</label><input type="text" name="campaign" value="launch_2026"></div></div><div class="field" style="margin-top:12px;"><label>Generated Tracking URL</label><input type="text" name="output" readonly></div><div style="margin-top:12px;"><button class="btn-cta" type="button" data-action="copy">Copy Tracking URL</button></div>""",
        ),
        ToolSpec(
            slug="seo-meta-generator",
            widget_id="tool-seo-meta",
            kr_title="SEO 메타태그 · 오픈그래프(OG) 코드 자동 생성기",
            kr_h1="SEO Meta Tag & Open Graph(OG) 코드 생성기",
            kr_desc="구글·네이버 검색 노출과 카카오톡·SNS 공유 미리보기에 최적화된 HTML 메타태그를 자동 생성하세요.",
            kr_guide="검색엔진 최적화(SEO)의 기본은 정확한 title, description, canonical, 그리고 카카오톡·페이스북 공유 미리보기를 결정하는 og:title / og:description 태그입니다. 입력 즉시 복사 가능한 HTML 코드를 생성합니다.",
            kr_faqs=[("title과 description 권장 길이는 얼마인가요?", "제목은 30~60자, 설명은 70~155자 이내로 핵심 키워드를 앞쪽에 배치하는 것이 좋습니다."), ("생성된 코드는 어디에 붙여넣나요?", "웹사이트 HTML 문서의 <head>와 </head> 태그 사이에 붙여넣으세요.")],
            en_title="Free SEO Meta Tag & Open Graph (OG) Generator",
            en_h1="SEO Meta Tag & Open Graph Generator",
            en_desc="Generate search-engine-friendly title, description, canonical, and Open Graph HTML tags for higher click-through rates.",
            en_guide="Build clean, valid HTML head tags to control how your pages appear on Google Search, X/Twitter, LinkedIn, and Slack previews.",
            en_faqs=[("Where should I paste the generated tags?", "Inside the <head>...</head> section of your HTML page."), ("Why is the canonical tag important?", "It prevents duplicate content penalties by telling search engines the preferred URL.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>페이지 제목 (Title)</label><input type="text" name="title" value="내 사이트 핵심 키워드 제목"></div><div class="field"><label>페이지 설명 (Description)</label><input type="text" name="desc" value="검색 결과에 표시될 120자 이내 매력적인 요약 문구"></div><div class="field"><label>대표 URL (Canonical)</label><input type="url" name="url" value="https://example.com/"></div></div><div class="field" style="margin-top:12px;"><label>생성된 HTML 코드</label><textarea name="output" rows="6" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div><div style="margin-top:12px;"><button class="btn-cta" type="button" data-action="copy">HTML 코드 복사</button></div>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>Page Title</label><input type="text" name="title" value="Best Free Online Tools Hub"></div><div class="field"><label>Meta Description</label><input type="text" name="desc" value="Fast, private browser tools for developers and marketers."></div><div class="field"><label>Canonical URL</label><input type="url" name="url" value="https://example.com/"></div></div><div class="field" style="margin-top:12px;"><label>Generated HTML Tags</label><textarea name="output" rows="6" readonly style="width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;background:#f8fafc;"></textarea></div><div style="margin-top:12px;"><button class="btn-cta" type="button" data-action="copy">Copy HTML Tags</button></div>""",
        ),
        ToolSpec(
            slug="color-converter",
            widget_id="tool-color",
            kr_title="색상 코드 변환기 (HEX ↔ RGB ↔ HSL 실시간 미리보기)",
            kr_h1="웹 디자인 색상 코드 변환기 (HEX · RGB · HSL)",
            kr_desc="HEX 컬러 코드를 RGB, HSL CSS 값으로 실시간 변환하고 색상 미리보기를 즉시 확인하세요.",
            kr_guide="CSS 스타일시트, 피그마(Figma), 브랜드 가이드 작업 시 HEX(#2563eb) 값을 RGB와 HSL 포맷으로 즉시 변환해 주는 디자이너·개발자용 유틸리티입니다.",
            kr_faqs=[("3자리 단축 HEX 코드(#fff)도 되나요?", "네, 3자리와 6자리 HEX 코드 모두 자동으로 인식해 변환합니다."), ("CSS에 바로 복사해 쓸 수 있나요?", "네, 표준 CSS 함수 형식(rgb(...), hsl(...))으로 출력됩니다.")],
            en_title="HEX to RGB & HSL Color Code Converter Online",
            en_h1="HEX to RGB & HSL CSS Color Converter",
            en_desc="Convert HEX color codes to CSS RGB and HSL values instantly with a live color swatch preview.",
            en_guide="Essential color utility for UI designers and front-end engineers to translate HEX codes into CSS-ready RGB and HSL formats in real time.",
            en_faqs=[("Does it support 3-digit shorthand HEX?", "Yes, shorthand values like #09f are automatically expanded."), ("Are outputs CSS-ready?", "Yes, both rgb() and hsl() values can be pasted directly into CSS.")],
            ui_html_kr="""<div class="calc-grid"><div class="field"><label>HEX 색상 코드</label><input type="text" name="hex" value="#2563eb"></div><div class="field"><label>미리보기</label><div data-out="swatch" style="height:44px;border-radius:8px;border:1px solid #cbd5e1;background:#2563eb;"></div></div></div><div class="result-strip"><div class="metric-box"><div class="metric-label">RGB</div><div class="metric-value" data-out="rgb" style="font-size:1.05rem;">rgb(37, 99, 235)</div></div><div class="metric-box"><div class="metric-label">HSL</div><div class="metric-value" data-out="hsl" style="font-size:1.05rem;">hsl(221, 83%, 53%)</div></div></div>""",
            ui_html_en="""<div class="calc-grid"><div class="field"><label>HEX Color Code</label><input type="text" name="hex" value="#2563eb"></div><div class="field"><label>Live Swatch</label><div data-out="swatch" style="height:44px;border-radius:8px;border:1px solid #cbd5e1;background:#2563eb;"></div></div></div><div class="result-strip"><div class="metric-box"><div class="metric-label">RGB</div><div class="metric-value" data-out="rgb" style="font-size:1.05rem;">rgb(37, 99, 235)</div></div><div class="metric-box"><div class="metric-label">HSL</div><div class="metric-value" data-out="hsl" style="font-size:1.05rem;">hsl(221, 83%, 53%)</div></div></div>""",
        ),
    ]


def generate_web_tool_pages(
    cfg: SiteConfig,
    dist: Path,
    *,
    is_sample_data: bool,
    base_layout_fn: Callable[..., str],
    adsense_slot_fn: Callable[[SiteConfig, str], str],
    faq_section_fn: Callable[[list[tuple[str, str]]], tuple[str, dict[str, Any]]],
    page_cls: type,
    esc_fn: Callable[[Any], str],
) -> tuple[list[Any], list[tuple[str, str]], list[tuple[str, str]]]:
    """Generate 24 SEO-rich browser utility pages (12 KR + 12 EN)."""
    specs = _tool_specs()
    kr_dir = dist / "tools"
    en_dir = dist / "en-tools"
    kr_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    kr_links = [(s.kr_title.split("(")[0].strip(), f"tools/{s.slug}.html") for s in specs]
    en_links = [(s.en_h1, f"en-tools/{s.slug}.html") for s in specs]
    pages: list[Any] = []

    for s in specs:
        # Korean page
        rel_kr = f"tools/{s.slug}.html"
        url_kr = f"{cfg.site_url}/{rel_kr}"
        faq_html, faq_ld = faq_section_fn(s.kr_faqs)
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in kr_links if h != rel_kr)
        body_kr = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#tools-hub">무료 웹 유틸리티</a> › {esc_fn(s.kr_h1)}</nav>
<h1>{esc_fn(s.kr_h1)}</h1>
<p class="lead">{esc_fn(s.kr_desc)}</p>
{adsense_slot_fn(cfg, f"tool-kr-{s.slug}-top")}
<section class="card" data-widget="{esc_fn(s.widget_id)}">
  <h2>100% 브라우저 로컬 실행 도구</h2>
  {s.ui_html_kr}
</section>
{adsense_slot_fn(cfg, f"tool-kr-{s.slug}-mid")}
<section class="card">
  <h2>사용 방법 및 보안 안내</h2>
  <p>{esc_fn(s.kr_guide)}</p>
</section>
{faq_html}
<section class="card"><h2>다른 무료 웹 유틸리티 도구</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_kr).write_text(
            base_layout_fn(
                cfg,
                title=s.kr_title,
                description=s.kr_desc,
                canonical_url=url_kr,
                body_html=body_kr,
                json_ld_objects=[{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": s.kr_h1, "url": url_kr, "applicationCategory": "UtilitiesApplication", "operatingSystem": "All", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "KRW"}}, faq_ld],
                asset_prefix="../",
                is_sample_data=is_sample_data,
            ),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_kr, url_kr, s.kr_title, s.kr_desc, "web_tools_kr"))

        # English global page
        rel_en = f"en-tools/{s.slug}.html"
        url_en = f"{cfg.site_url}/{rel_en}"
        faq_html_en, faq_ld_en = faq_section_fn(s.en_faqs)
        related_en = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in en_links if h != rel_en)
        body_en = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-tools-hub">Free Online Tools</a> › {esc_fn(s.en_h1)}</nav>
<h1>{esc_fn(s.en_h1)}</h1>
<p class="lead">{esc_fn(s.en_desc)}</p>
{adsense_slot_fn(cfg, f"tool-en-{s.slug}-top")}
<section class="card" data-widget="{esc_fn(s.widget_id)}">
  <h2>Instant Client-Side Utility (Zero Server Uploads)</h2>
  {s.ui_html_en}
</section>
{adsense_slot_fn(cfg, f"tool-en-{s.slug}-mid")}
<section class="card">
  <h2>How It Works &amp; Privacy Guarantee</h2>
  <p>{esc_fn(s.en_guide)}</p>
</section>
{faq_html_en}
<section class="card"><h2>More Free Online Web Utilities</h2><div class="link-grid">{related_en}</div></section>
"""
        (dist / rel_en).write_text(
            base_layout_fn(
                cfg,
                title=s.en_title,
                description=s.en_desc,
                canonical_url=url_en,
                body_html=body_en,
                json_ld_objects=[{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": s.en_h1, "url": url_en, "applicationCategory": "UtilitiesApplication", "operatingSystem": "All", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}, faq_ld_en],
                asset_prefix="../",
                is_sample_data=is_sample_data,
            ),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_en, url_en, s.en_title, s.en_desc, "web_tools_en"))

    return pages, kr_links, en_links
