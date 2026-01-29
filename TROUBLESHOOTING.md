# 🔧 Solucionando Erros Comuns

## ❌ Erro 403: Permission denied

**Causa:** O GitHub Actions não tem permissão para fazer push no repositório.

**Solução:**

### 1. Configure as permissões do repositório

1. Vá em: **Settings** > **Actions** > **General**
2. Role até **Workflow permissions**
3. Selecione: **Read and write permissions** ✅
4. Marque: **Allow GitHub Actions to create and approve pull requests** ✅
5. Clique em **Save**

### 2. Verifique se o workflow tem permissões

O arquivo `.github/workflows/update-heatmap.yml` já deve ter:

```yaml
permissions:
  contents: write
```

### 3. Certifique-se de que o branch correto existe

O workflow usa `main` por padrão. Se seu branch principal é `master`, mude:

```yaml
on:
  push:
    branches: [ master ]  # ← mude aqui
```

## ⚠️ Warning: set-output is deprecated

**Causa:** Comando antigo do GitHub Actions.

**Solução:** O warning não afeta o funcionamento, mas se quiser resolver:
- Ignore por enquanto, é apenas um aviso
- O GitHub Actions vai descontinuar esse comando no futuro

## ❌ Erro: Unable to access repository

**Causa:** O token não tem as permissões corretas.

**Solução:**

1. **Para GitHub Actions (automático):**
   - Já está configurado corretamente no workflow atualizado
   - Não precisa fazer nada

2. **Para uso local:**
   - Crie um token em: https://github.com/settings/tokens
   - Dê a permissão: `read:user`
   - Antes de rodar o script:
   ```bash
   export GITHUB_TOKEN="seu_token_aqui"
   export USERNAME="ehurafa"
   python generate_heatmap.py
   ```

## 🔍 Como debugar

### Ver logs completos do workflow:

1. Vá em **Actions** no seu repositório
2. Clique no workflow que falhou
3. Clique em **Jobs to update datas**
4. Expanda cada step para ver os detalhes

### Testar localmente antes de fazer commit:

```bash
# Instale as dependências
pip install requests

# Exporte seu token (opcional, mas recomendado)
export GITHUB_TOKEN="seu_token_aqui"
export USERNAME="ehurafa"

# Rode o script
python generate_heatmap.py

# Se funcionar, o arquivo github-heatmap.svg será criado
ls -la github-heatmap.svg
```

## ✅ Checklist de Configuração

- [ ] Repositório criado com nome igual ao username (`ehurafa`)
- [ ] Repositório é **público**
- [ ] Arquivos commitados:
  - [ ] `generate_heatmap.py`
  - [ ] `.github/workflows/update-heatmap.yml`
  - [ ] `README.md`
- [ ] Workflow permissions em **Read and write** ✅
- [ ] Branch correto (`main` ou `master`)
- [ ] Actions ativadas no repositório

## 🚀 Testando manualmente

Você pode rodar o workflow manualmente:

1. Vá em **Actions**
2. Selecione **Update GitHub Heatmap**
3. Clique em **Run workflow**
4. Selecione o branch
5. Clique em **Run workflow**

Isso vai executar imediatamente sem esperar o cron diário.

## 📝 Estrutura correta dos arquivos

```
ehurafa/                              # ← Nome do repositório
├── .github/
│   └── workflows/
│       └── update-heatmap.yml       # ← Deve estar aqui!
├── generate_heatmap.py              # ← Na raiz
├── github-heatmap.svg               # ← Será criado automaticamente
└── README.md                        # ← Na raiz
```

## 💡 Dicas

1. **Primeira execução**: Execute manualmente para testar
2. **Aguarde**: O cron roda todo dia às 00:00 UTC (21:00 BRT)
3. **Commit inicial**: O primeiro push pode precisar de aprovação manual
4. **Branch protegido**: Se seu branch main é protegido, você precisará ajustar as regras

## 🆘 Ainda com problemas?

Se nada funcionar:

1. Delete o repositório
2. Recrie do zero
3. Configure as permissões ANTES de adicionar os arquivos
4. Faça o primeiro commit com todos os arquivos de uma vez

---

💬 Se precisar de mais ajuda, me chama!
