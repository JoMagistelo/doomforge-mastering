# Publicar este ZIP como repositorio nuevo

El nombre sugerido es `doomforge-mastering`.

## Opción rápida con GitHub CLI

Desde la carpeta descomprimida:

```powershell
git init
git add .
git commit -m "feat: initial DoomForge mastering studio"
git branch -M main
gh auth login
gh repo create JoMagistelo/doomforge-mastering --public --source=. --remote=origin --push
```

Si prefieres mantenerlo privado al inicio, cambia `--public` por `--private`.

Después, en cualquier otra máquina / VS Code:

```powershell
git clone https://github.com/JoMagistelo/doomforge-mastering.git
cd doomforge-mastering
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python main.py
```
