#!/usr/bin/env python3
"""Run the checks named after the suite and write test-results/<suite>/junit.xml.

    .aidev/run-checks.py <suite> <step>...

The repository is one static page (index.html, bootstrap.min.css, favicon.ico,
images/) with no build, no package manager and no tests, so the steps are the
static checks such a page allows. One junit case per checked file or step:

  html    index.html parses, and every non-void element it opens is closed in
          order (a stray or missing close tag fails, naming the line)
  assets  every repository-relative reference in index.html (src=, href=,
          CSS url()) names a file that exists; absolute URLs are not fetched
  svg     every images/*.svg is well-formed XML

Not run: the deploy jobs (aws s3 sync to S3 + CloudFront) and any check of
the external links and CDNs the page loads (network).

Runs offline in the image the profile pins (python:3-alpine), standard library
only.
"""
import glob
import html.parser
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
# Unclosed elements already on develop at onboarding (2026-10-30, e097e9a):
# the footer's two outer <div>s are never closed; </body> closes them. Keyed by
# tag and class, not line, so edits elsewhere don't shift them. Remove an entry
# once the page closes that element. See .aidev/README.md.
KNOWN_UNCLOSED = {("div", "footer layout__footer"), ("div", "footer__inner")}
# Elements whose end tag HTML lets an author omit.
OPTIONAL_END = {"p", "li", "dt", "dd", "option", "optgroup", "tr", "td", "th",
                "thead", "tbody", "tfoot", "colgroup", "rt", "rp", "html", "head", "body"}


class Balance(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.refs, self.known = [], [], [], []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value:
                self.refs.append((self.getpos()[0], value))
            if name == "style" and value:
                self.refs += [(self.getpos()[0], u) for u in re.findall(r"url\(['\"]?([^'\")]+)", value)]
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0], dict(attrs).get("class") or ""))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID:
            return
        if not any(t == tag for t, _, _ in self.stack):
            self.errors.append(f"line {line}: </{tag}> closes nothing open")
            return
        while self.stack:
            t, opened, cls = self.stack.pop()
            if t == tag:
                return
            if (t, cls) in KNOWN_UNCLOSED:
                self.known.append(f"<{t} class=\"{cls}\"> opened at line {opened} (known, excluded)")
            elif t not in OPTIONAL_END:
                self.errors.append(f"line {line}: </{tag}> closes <{t}> opened at line {opened} first")

    def handle_data(self, data):
        if self.stack and self.stack[-1][0] == "style":
            self.refs += [(self.getpos()[0], u) for u in re.findall(r"url\(['\"]?([^'\")]+)", data)]


def check_html():
    p = Balance()
    with open("index.html", encoding="utf-8") as f:
        p.feed(f.read())
    p.close()
    errors = p.errors + [f"<{t}> opened at line {line} is never closed"
                         for t, line, cls in p.stack if t not in OPTIONAL_END and (t, cls) not in KNOWN_UNCLOSED]
    for note in p.known:
        print(f"     note: {note}")
    return errors, p.refs


def is_local(ref):
    return not re.match(r"^([a-z][a-z0-9+.-]*:|//|#)", ref, re.I) and not ref.startswith("{{")


def main():
    if len(sys.argv) < 2:
        sys.exit(f"usage: {sys.argv[0]} <suite> <step>...")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    suite = sys.argv[1]
    out = os.path.join("test-results", suite)
    os.makedirs(out, exist_ok=True)
    cases = []

    def record(name, t0, failures):
        cases.append((name, round(time.time() - t0, 3), failures))
        print(f"{'FAIL' if failures else 'ok  '} {name}")
        for msg in failures:
            print(f"     {msg}")

    for step in sys.argv[2:]:
        t0 = time.time()
        if step == "html":
            try:
                errors, _ = check_html()
            except (OSError, UnicodeDecodeError) as exc:
                errors = [str(exc)]
            record("html/index.html", t0, errors)
        elif step == "assets":
            try:
                _, refs = check_html()
                missing = []
                for line, ref in refs:
                    if is_local(ref):
                        path = ref.split("#")[0].split("?")[0].lstrip("/")
                        if path and not os.path.exists(path):
                            missing.append(f"line {line}: {ref} does not exist")
            except (OSError, UnicodeDecodeError) as exc:
                missing = [str(exc)]
            record("assets/index.html", t0, missing)
        elif step == "svg":
            for svg in sorted(glob.glob("images/*.svg")):
                t0 = time.time()
                try:
                    ET.parse(svg)
                    errors = []
                except ET.ParseError as exc:
                    errors = [f"{svg}: {exc}"]
                record(f"svg/{os.path.basename(svg)}", t0, errors)
        else:
            record(step, t0, [f"unknown step: {step}"])

    failed = sum(1 for c in cases if c[2])
    with open(os.path.join(out, "junit.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<testsuite name="signup-hive-io.{escape(suite)}" tests="{len(cases)}" failures="{failed}" errors="0" skipped="0">\n')
        for name, secs, failures in cases:
            f.write(f'<testcase classname="signup-hive-io.{escape(suite)}" name={quoteattr(name)} time="{secs}">')
            if failures:
                f.write(f'<failure message={quoteattr(failures[0])}>{escape(chr(10).join(failures))}</failure>')
            f.write("</testcase>\n")
        f.write("</testsuite>\n")
    print(f"junit: {out}/junit.xml ({len(cases)} cases, {failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
