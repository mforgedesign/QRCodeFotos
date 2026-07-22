# QR Fotos — Enviar fotos do celular

**Data:** 2026-07-22
**Estado:** Design aprovado para planejamento

## Objetivo

Adicionar à página de captura de todos os eventos QR Fotos uma segunda forma de participação: além de abrir a câmera no navegador, o convidado poderá selecionar e enviar várias imagens já existentes no celular.

## Restrições de compatibilidade

A atualização não poderá alterar:

- o `EVENT_ID` de nenhum evento;
- as URLs públicas ou os diretórios publicados;
- os destinos codificados nos QR Codes existentes;
- os endpoints atuais da API;
- as galerias, fotos ou metadados já armazenados;
- o comportamento atual de captura pela câmera, incluindo download local da nova captura.

## Interface

A tela inicial terá duas ações:

1. **Abrir Câmera** — ação principal, preservando o fluxo atual.
2. **Enviar do Celular** — ação secundária, abrindo o seletor nativo de arquivos/imagens.

Os textos de instrução serão atualizados para explicar os dois caminhos. Ambos solicitarão o nome ou apelido do convidado antes de continuar.

O modal de nome será neutro e adaptará a ação de confirmação ao caminho escolhido. O botão não prometerá abrir a câmera quando o convidado tiver escolhido enviar arquivos.

## Fluxo da câmera

1. Convidado toca em **Abrir Câmera**.
2. Informa nome ou apelido.
3. O navegador solicita permissão da câmera.
4. Convidado captura e revisa a foto.
5. Ao confirmar, a imagem é baixada no aparelho e enviada ao evento, como ocorre atualmente.

## Fluxo de envio do celular

1. Convidado toca em **Enviar do Celular**.
2. Informa nome ou apelido.
3. O seletor nativo permite escolher várias imagens (`multiple`, `accept="image/*"`).
4. O sistema valida cada arquivo e o processa de forma sequencial para limitar memória e tráfego.
5. Formatos que o navegador consegue decodificar são normalizados para JPEG por canvas antes do upload, respeitando dimensão máxima de 1920 pixels e qualidade equivalente à captura atual.
6. Cada imagem é enviada ao mesmo endpoint do evento, com o mesmo campo `nome`.
7. A interface exibe progresso agregado: quantidade concluída, total e falhas.
8. Ao terminar, informa quantas imagens foram enviadas e quantas falharam.

Imagens selecionadas do celular não serão baixadas novamente para o aparelho.

## Validação e erros

- Aceitar somente arquivos cujo MIME comece com `image/`.
- Rejeitar arquivos acima de 10 MB antes do envio, alinhado ao limite do backend.
- Se uma imagem não puder ser decodificada ou convertida, registrar falha individual e continuar com as demais.
- Cada upload terá timeout de 15 segundos, preservando a política atual.
- O seletor será limpo após cada lote para permitir selecionar novamente os mesmos arquivos.
- Negar permissão da câmera não impedirá o uso de **Enviar do Celular**.
- O fluxo não armazenará imagens em `localStorage` ou outro armazenamento persistente do navegador.

## Arquitetura da alteração

A lógica será implementada no template canônico da fábrica e propagada para os `index.html` dos eventos existentes, preservando os valores específicos de cada evento: título, subtítulo, monograma, paleta e `EVENT_ID`.

A galeria e o backend não precisam mudar: o envio continuará usando `multipart/form-data`, campo `image` e campo `nome` no endpoint `/upload/<EVENT_ID>`.

## Eventos existentes no escopo

- `anna-carolina-15-anos`
- `giorgia-15-anos`
- `xv-giovana`
- `casamento-ana-pedro`
- `festa-joao`

A página raiz do repositório será inspecionada separadamente e só será alterada se ela usar o mesmo fluxo de captura.

## Verificação

Antes da publicação:

1. Confirmar que todos os `EVENT_ID` e URLs permanecem idênticos.
2. Validar o JavaScript inline de cada página com `node --check`.
3. Executar testes estruturais para os dois botões, `input[type=file]`, `multiple`, aceitação de imagens e rotas de ação.
4. Testar em viewport móvel:
   - câmera continua abrindo;
   - seletor de arquivos abre sem pedir câmera;
   - seleção múltipla é processada;
   - progresso e falhas aparecem;
   - retorno à tela inicial funciona.
5. Fazer upload real em evento temporário de teste, verificar listagem pela API e remover imediatamente os arquivos e metadados de teste.
6. Publicar no GitHub Pages e confirmar HTTP 200 para cada URL existente.
7. Decodificar ou comparar os destinos dos QR Codes existentes para provar que nenhuma URL mudou.

## Critérios de aceite

- O convidado vê e consegue usar as duas opções.
- O envio do celular aceita várias imagens no mesmo lote.
- O nome do convidado continua agrupando as fotos na galeria.
- Uma falha individual não cancela o restante do lote.
- O fluxo da câmera permanece funcional.
- Nenhum QR Code precisa ser reimpresso ou regenerado.
- Nenhuma foto ou metadata existente é removida ou regravada.
