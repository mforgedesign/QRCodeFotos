# Enviar Fotos do Celular Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar seleção e envio múltiplo de imagens do celular sem alterar URLs, IDs de eventos, QR Codes, fotos existentes ou o fluxo atual da câmera.

**Architecture:** Cada página continuará autônoma, com JavaScript inline. O modal de nome guardará a ação escolhida (`camera` ou `files`); o fluxo de arquivos normalizará imagens sequencialmente para JPEG e reutilizará o mesmo contrato `multipart/form-data` do backend. O template canônico e todas as páginas de captura existentes receberão a mesma lógica, preservando configuração e identidade visual próprias.

**Tech Stack:** HTML5, CSS, JavaScript sem dependências, Canvas API, File API, Fetch API, Python `unittest`, Node.js para verificação sintática, GitHub Pages.

---

## Estrutura de arquivos

- Criar `tests/test_device_upload.py`: contrato estrutural comum e preservação dos `EVENT_ID`.
- Modificar `/root/.hermes/workspace/templates/fotoqr-factory/template-index.html`: fonte canônica para eventos futuros.
- Modificar `index.html` e os cinco `<evento>/index.html`: interface e lógica de envio atualizadas.
- Não modificar `galeria.html`, `server.js`, uploads, metadados ou QR Codes.

### Task 1: Testes de contrato em estado vermelho

**Files:**
- Create: `tests/test_device_upload.py`

- [ ] **Step 1: Criar teste estrutural parametrizado**

O teste deve ler o template, a raiz e os cinco eventos; exigir dois botões distintos, `input` múltiplo, funções de normalização/lote, limite de 10 MB, envio sequencial e os IDs atuais:

```python
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path('/root/.hermes/workspace/templates/fotoqr-factory/template-index.html')
PAGES = {
    ROOT / 'index.html': None,
    ROOT / 'anna-carolina-15-anos/index.html': 'anna-carolina-15-anos',
    ROOT / 'giorgia-15-anos/index.html': 'giorgia-15-anos',
    ROOT / 'xv-giovana/index.html': 'xv-giovana',
    ROOT / 'casamento-ana-pedro/index.html': 'casamento-ana-pedro',
    ROOT / 'festa-joao/index.html': 'festa-joao',
    TEMPLATE: 'xv-giovana',
}

class DeviceUploadContract(unittest.TestCase):
    def test_all_pages_expose_both_entry_points(self):
        for path in PAGES:
            html = path.read_text(encoding='utf-8')
            self.assertIn("showNameModal('camera')", html, path)
            self.assertIn("showNameModal('files')", html, path)
            self.assertRegex(html, r'<input[^>]+id="file-input"[^>]+accept="image/\*"[^>]+multiple')

    def test_batch_contract_is_present(self):
        for path in PAGES:
            html = path.read_text(encoding='utf-8')
            for token in ('processSelectedFiles', 'normalizeImageFile',
                          'uploadImageBlob', 'MAX_FILE_BYTES',
                          '10 * 1024 * 1024', 'for (const file of files)'):
                self.assertIn(token, html, f'{path}: {token}')

    def test_event_ids_are_unchanged(self):
        for path, event_id in PAGES.items():
            if event_id is None:
                continue
            html = path.read_text(encoding='utf-8')
            self.assertIn(f'const EVENT_ID = "{event_id}";', html, path)

    def test_inline_javascript_parses(self):
        for path in PAGES:
            html = path.read_text(encoding='utf-8')
            scripts = re.findall(r'<script>([\s\S]*?)</script>', html)
            self.assertTrue(scripts, path)
            with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
                f.write('\n'.join(scripts))
                script_path = f.name
            result = subprocess.run(['node', '--check', script_path], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, f'{path}: {result.stderr}')

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Executar e confirmar vermelho**

Run: `python3 -m unittest tests/test_device_upload.py -v`
Expected: falhas por ausência de `showNameModal('camera')`, `file-input` e funções de lote.

- [ ] **Step 3: Commit do teste vermelho**

```bash
git add tests/test_device_upload.py
git commit -m "test: define contrato de envio do celular"
```

### Task 2: Interface e seleção da ação

**Files:**
- Modify: `/root/.hermes/workspace/templates/fotoqr-factory/template-index.html`
- Modify: `index.html`
- Modify: `anna-carolina-15-anos/index.html`
- Modify: `giorgia-15-anos/index.html`
- Modify: `xv-giovana/index.html`
- Modify: `casamento-ana-pedro/index.html`
- Modify: `festa-joao/index.html`

- [ ] **Step 1: Adicionar estilos compartilhados**

Adicionar `.entry-actions`, `.btn-secondary`, `.upload-status`, `.upload-progress` e `.upload-progress-fill`, usando as variáveis de cor existentes e layout em coluna no celular.

- [ ] **Step 2: Tornar o modal neutro**

Trocar o botão fixo por:

```html
<button class="btn-primary" id="btn-confirm-name" style="width:100%;" onclick="confirmName()">Continuar</button>
```

- [ ] **Step 3: Adicionar as duas ações e o seletor oculto**

```html
<div class="entry-actions">
  <button class="btn-primary" id="btn-start" onclick="showNameModal('camera')"><span class="btn-icon">📷</span> Abrir Câmera</button>
  <button class="btn-secondary" id="btn-files" onclick="showNameModal('files')"><span class="btn-icon">▣</span> Enviar do Celular</button>
</div>
<input type="file" id="file-input" accept="image/*" multiple hidden>
```

- [ ] **Step 4: Adicionar estado visual de progresso**

```html
<div id="upload-status" class="upload-status" aria-live="polite" hidden>
  <strong id="upload-status-title">Enviando fotos</strong>
  <span id="upload-status-text">Preparando...</span>
  <div class="upload-progress"><div id="upload-progress-fill" class="upload-progress-fill"></div></div>
</div>
```

- [ ] **Step 5: Implementar despacho da ação**

```javascript
let pendingAction = "camera";
function showNameModal(action = "camera") {
  pendingAction = action;
  document.getElementById("btn-confirm-name").textContent = action === "files" ? "Continuar para Selecionar Fotos" : "Confirmar e Abrir Câmera";
  document.getElementById("name-modal").style.display = "block";
  setTimeout(() => document.getElementById("guest-name").focus(), 300);
}
function confirmName() {
  guestName = document.getElementById("guest-name").value.trim() || "Anônimo";
  document.getElementById("name-modal").style.display = "none";
  if (pendingAction === "files") document.getElementById("file-input").click();
  else startCamera();
}
```

### Task 3: Pipeline sequencial de imagens

**Files:** mesmos sete HTML da Task 2.

- [ ] **Step 1: Definir limites e listener**

```javascript
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_IMAGE_DIMENSION = 1920;
document.getElementById("file-input").addEventListener("change", event => {
  const files = Array.from(event.target.files || []);
  event.target.value = "";
  if (files.length) processSelectedFiles(files);
});
```

- [ ] **Step 2: Normalizar uma imagem para JPEG**

Implementar `normalizeImageFile(file)` com `createImageBitmap(file, { imageOrientation: "from-image" })` e fallback para `Image` + `URL.createObjectURL`; calcular escala máxima de 1920 px; desenhar em canvas temporário; retornar `canvas.toBlob(..., "image/jpeg", 0.85)`; fechar bitmap e revogar URL quando aplicável.

- [ ] **Step 3: Extrair upload reutilizável**

```javascript
async function uploadImageBlob(blob, filename = "capture.jpg") {
  const fd = new FormData();
  fd.append("image", blob, filename);
  fd.append("nome", guestName);
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 15000);
  try {
    const response = await fetch(API_URL, { method: "POST", body: fd, signal: ctrl.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
  } finally {
    clearTimeout(timeout);
  }
}
```

- [ ] **Step 4: Processar lote sem interromper em falha individual**

Implementar `processSelectedFiles(files)` com `for (const file of files)`, validação `image/*` e 10 MB, normalização, `await uploadImageBlob`, contadores de sucesso/falha, atualização percentual e mensagem final. Durante o lote, desabilitar as duas ações; no fim, reabilitar ambas e manter a página pronta para novo lote.

- [ ] **Step 5: Reutilizar upload no fluxo da câmera**

Substituir o bloco duplicado de `fetch` em `confirmPhoto()` por:

```javascript
const blob = await canvasToBlob(captureCanvas, "image/jpeg", 0.85);
await uploadImageBlob(blob, "capture.jpg");
serverSaved = true;
```

A criação do download local permanece exclusivamente em `confirmPhoto()`.

- [ ] **Step 6: Rodar testes verdes**

Run: `python3 -m unittest tests/test_device_upload.py -v`
Expected: quatro testes aprovados para sete páginas.

- [ ] **Step 7: Commit da implementação**

```bash
git add index.html */index.html tests/test_device_upload.py
git commit -m "feat: permite enviar fotos do celular"
```

O template canônico fica fora do repositório e deve ser verificado no mesmo comando de teste.

### Task 4: QA móvel e upload isolado

- [ ] **Step 1: Servir a página localmente**

Run: `python3 -m http.server 8766 --bind 127.0.0.1` no repositório, em processo controlado.

- [ ] **Step 2: Verificar DOM e comportamento em viewport móvel**

Abrir a página com navegador automatizado; confirmar os dois botões, modal adaptável, input múltiplo e ausência de solicitação de câmera ao escolher arquivos. Interceptar `window.fetch` e enviar dois arquivos de imagem sintéticos para validar lote, progresso e resumo sem gravar em evento real.

- [ ] **Step 3: Testar API com evento temporário**

Gerar JPEG mínimo e executar upload para `test-device-upload-20260722`; consultar `/photos/test-device-upload-20260722`; remover somente `/var/www/xv-giovana/uploads/test-device-upload-20260722/`; consultar novamente e exigir total zero.

- [ ] **Step 4: Confirmar invariantes**

Comparar a lista de `EVENT_ID`, URLs públicas e conteúdo dos PNGs em `projects/fotoqr-factory/qrcodes/` antes/depois. Nenhum QR deve ser modificado.

### Task 5: Publicação e verificação

- [ ] **Step 1: Push**

Run: `git push origin main`
Expected: branch `main` atualizada sem erro.

- [ ] **Step 2: Aguardar GitHub Pages**

Consultar o commit publicado pela API/HTML até a nova marcação `id="file-input"` aparecer, com timeout limitado.

- [ ] **Step 3: Verificar todas as URLs**

Exigir HTTP 200 na raiz e nos cinco eventos; extrair cada HTML publicado e confirmar os dois botões, seleção múltipla e `EVENT_ID` correspondente.

- [ ] **Step 4: Verificar backend e dados existentes**

Exigir `https://qrfotos.duckdns.org/health` com estado saudável. Comparar contagens por evento antes/depois; nenhuma foto existente pode desaparecer.

- [ ] **Step 5: Relatório final**

Informar URLs preservadas, páginas atualizadas, testes executados, upload temporário removido e confirmação de que nenhum QR Code foi regenerado.
