# Git identity check

## Problema detectado

Este repo tiene una separacion entre identidad de autor de commits, remoto GitHub y autenticacion real de push:

- La configuracion **local** del repo ya usa la identidad correcta:
  - `user.name=Jose Gonzalez Oliva`
  - `user.email=josegolivadev@gmail.com`
- La configuracion **global** del equipo sigue con email antiguo:
  - `josematerupm@gmail.com`
- Los commits recientes muestran ese email antiguo como autor.
- `gh auth status` indica una cuenta activa `Josegodev` con token invalido.
- `origin` apunta a `git@github.com:Josegodev/LOCALES.git`; ese owner no se puede afirmar con seguridad que sea el repo correcto de `josegolivadev`.

## Comandos de verificacion

```bash
git config --show-origin --get user.name
git config --show-origin --get user.email
git config --global --get user.name
git config --global --get user.email
git config --local --get user.name
git config --local --get user.email
git remote -v
git branch --show-current
git log -5 --pretty=format:"%h %an <%ae> %s"
gh auth status
```

## Configuracion correcta para este repo

```bash
git config user.name "Jose Gonzalez Oliva"
git config user.email "josegolivadev@gmail.com"
```

Verificacion:

```bash
git config --local user.name
git config --local user.email
```

## Diferencia entre author y cuenta real de push

- `git config user.email` controla el **autor** que queda grabado en cada commit.
- La cuenta que hace `git push` depende de:
  - la URL del remoto (`ssh` o `https`)
  - las credenciales activas en `ssh-agent`, Git Credential Manager o `gh`
  - la cuenta conectada en GitHub/Vercel

Dicho simple:

- puedes firmar commits con `josegolivadev@gmail.com`
- y aun asi estar empujando a GitHub con otra cuenta si el remoto o las credenciales siguen mal

## Estado observado en esta auditoria

- Local repo identity: correcta
- Global identity: antigua
- Recent commit authors: antiguos
- GitHub CLI auth: invalida para `Josegodev`
- Remote origin: ambiguo, requiere verificacion manual

## Acciones manuales recomendadas

### 1. Corregir identidad global si quieres evitar repetir el problema

```bash
git config --global user.name "Jose Gonzalez Oliva"
git config --global user.email "josegolivadev@gmail.com"
```

### 2. Revisar el remoto origin

No se cambia automaticamente mientras el owner correcto no sea inequívoco.

Si confirmas que el repo correcto es `josegolivadev/LOCALES`, ejecuta:

```bash
git remote set-url origin https://github.com/josegolivadev/LOCALES.git
```

Si prefieres SSH:

```bash
git remote set-url origin git@github.com:josegolivadev/LOCALES.git
```

### 3. Reautenticar GitHub CLI

Estado actual observado:

- cuenta activa: `Josegodev`
- token invalido

Comandos sugeridos:

```bash
gh auth logout -h github.com -u Josegodev
gh auth login -h github.com
gh auth status
```

Despues autenticate con la cuenta correcta asociada a `josegolivadev@gmail.com`.

### 4. Limpieza de credenciales HTTPS

Solo aplica si usas remoto HTTPS o si sospechas que Git esta reutilizando credenciales antiguas.

Comando:

```bash
printf "protocol=https\nhost=github.com\n" | git credential reject
```

Impacto:

- no borra commits
- no toca el repo
- solo obliga a Git a pedir credenciales nuevas la proxima vez que haga push por HTTPS

### 5. Ultimo commit con email antiguo

No se reescribe historial automaticamente.

Si quieres corregir **solo el ultimo commit**:

```bash
git commit --amend --reset-author
git push --force-with-lease
```

Hazlo solo si entiendes el impacto de reescribir el commit ya publicado.

## Checklist para Vercel

En Vercel revisa:

- `Project -> Settings -> Git -> Connected Git Repository`
- owner del repo
- nombre del repo
- rama conectada

Confirmar que apunta a:

- `josegolivadev/LOCALES`
- o al repo correcto confirmado manualmente

Si Vercel sigue enlazado al owner antiguo, aunque Git local este bien, el despliegue seguira yendo al repo equivocado.

## Relacionado

- [[README]]
- [[LOCAL_DEPLOYMENT]]
- [[GLOSSARY]]
