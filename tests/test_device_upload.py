import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(
    os.environ.get(
        'FOTOQR_TEMPLATE',
        '/root/.hermes/workspace/templates/fotoqr-factory/template-index.html',
    )
)
PAGES = {
    ROOT / 'index.html': None,
    ROOT / 'anna-carolina-15-anos/index.html': 'anna-carolina-15-anos',
    ROOT / 'giorgia-15-anos/index.html': 'giorgia-15-anos',
    ROOT / 'xv-giovana/index.html': 'xv-giovana',
    ROOT / 'casamento-ana-pedro/index.html': 'casamento-ana-pedro',
    ROOT / 'festa-joao/index.html': 'festa-joao',
}
if TEMPLATE.exists():
    PAGES[TEMPLATE] = 'xv-giovana'


class DeviceUploadContract(unittest.TestCase):
    def test_all_pages_expose_both_entry_points(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = path.read_text(encoding='utf-8')
                self.assertIn("showNameModal('camera')", html)
                self.assertIn("showNameModal('files')", html)
                self.assertRegex(
                    html,
                    r'<input[^>]+id="file-input"[^>]+accept="image/\*"[^>]+multiple',
                )

    def test_batch_pipeline_validates_normalizes_and_uploads_sequentially(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = path.read_text(encoding='utf-8')
                for token in (
                    'const MAX_FILE_BYTES = 10 * 1024 * 1024;',
                    'const MAX_BATCH_FILES = 20;',
                    'const MAX_SOURCE_PIXELS = 60_000_000;',
                    'const DECODE_TIMEOUT_MS = 15000;',
                    'async function inspectImageDimensions(file)',
                    'async function normalizeImageFile(file)',
                    'async function uploadImageBlob(blob, filename = "capture.jpg")',
                    'async function processSelectedFiles(files)',
                    'for (const [index, file] of files.entries())',
                    'file.type.startsWith("image/")',
                    'file.size > MAX_FILE_BYTES',
                    'index >= MAX_BATCH_FILES',
                    'await uploadImageBlob(blob, makeNeutralFilename(index))',
                    'finally {\n    isUploading = false;',
                    'renderUploadFailures(failures)',
                    'upload-failure-list',
                ):
                    self.assertIn(token, html, token)
                self.assertNotIn('`${safeBaseName}.jpg`', html)

    def test_event_ids_and_upload_endpoints_are_unchanged(self):
        expected_api_expressions = {
            ROOT / 'index.html': "'https://qrfotos.duckdns.org/upload'",
            ROOT / 'anna-carolina-15-anos/index.html': '"https://qrfotos.duckdns.org/upload/"+EVENT_ID',
            ROOT / 'giorgia-15-anos/index.html': '"https://qrfotos.duckdns.org/upload/"+EVENT_ID',
            ROOT / 'xv-giovana/index.html': '"https://qrfotos.duckdns.org/upload/"+EVENT_ID',
            ROOT / 'casamento-ana-pedro/index.html': '"https://qrfotos.duckdns.org/upload/"+EVENT_ID',
            ROOT / 'festa-joao/index.html': '"https://qrfotos.duckdns.org/upload/"+EVENT_ID',
        }
        if TEMPLATE.exists():
            expected_api_expressions[TEMPLATE] = '"https://qrfotos.duckdns.org/upload/"+EVENT_ID'
        for path, event_id in PAGES.items():
            with self.subTest(path=path):
                html = path.read_text(encoding='utf-8')
                if event_id is not None:
                    match = re.search(r'const EVENT_ID\s*=\s*"([^"]+)";', html)
                    assert match is not None
                    self.assertEqual(event_id, match.group(1))
                api_match = re.search(r'const API_URL\s*=\s*([^;]+);', html)
                assert api_match is not None
                api_expression = re.sub(r'\s+', '', api_match.group(1))
                self.assertEqual(expected_api_expressions[path], api_expression)

    def test_inline_javascript_parses(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = path.read_text(encoding='utf-8')
                scripts = re.findall(r'<script>([\s\S]*?)</script>', html)
                self.assertTrue(scripts)
                with tempfile.NamedTemporaryFile(
                    'w', suffix='.js', encoding='utf-8'
                ) as script_file:
                    script_file.write('\n'.join(scripts))
                    script_file.flush()
                    result = subprocess.run(
                        ['node', '--check', script_file.name],
                        capture_output=True,
                        text=True,
                    )
                self.assertEqual(0, result.returncode, result.stderr)

    def test_device_batch_never_downloads_selected_files(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = path.read_text(encoding='utf-8')
                batch = html.split('async function processSelectedFiles(files)', 1)[1]
                batch = batch.split('async function confirmPhoto()', 1)[0]
                self.assertNotIn('document.createElement("a")', batch)
                camera = html.rsplit('async function confirmPhoto()', 1)[1]
                self.assertIn('document.createElement("a")', camera)


if __name__ == '__main__':
    unittest.main()
