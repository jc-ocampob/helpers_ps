# Flujo de contribución

Este repositorio utiliza un flujo de trabajo basado en ramas, Pull Requests y revisión obligatoria para mantener la calidad del paquete y evitar cambios no controlados en `main`.

La rama principal del proyecto es:

```text
main
```

Nadie debe trabajar directamente sobre `main`, excepto el maintainer principal del paquete en casos puntuales o urgentes.

---

## Reglas generales

1. Toda nueva funcionalidad debe desarrollarse en una rama propia.
2. Toda corrección de bug debe desarrollarse en una rama propia.
3. Todo cambio que afecte funciones públicas debe actualizar la documentación.
4. Todo Pull Request que modifique código crítico o documentación debe ser revisado por el code owner.
5. El merge a `main` debe realizarse únicamente después de recibir aprobación.
6. Todo cambio en `main` actualiza automáticamente la documentación publicada en GitHub Pages.

---

## Convención de ramas

Usar nombres descriptivos y en minúsculas.

### Nueva funcionalidad

```bash
feature/nombre-funcionalidad
```

Ejemplos:

```bash
feature/bar-stack-total
feature/line-custom-labels
feature/boxplot-last-value
```

### Corrección de bug

```bash
fix/nombre-bug
```

Ejemplos:

```bash
fix/legend-duplicate-labels
fix/bar-negative-labels
fix/mkdocs-api-reference
```

### Documentación

```bash
docs/nombre-documentacion
```

Ejemplos:

```bash
docs/graph-bar-examples
docs/update-quick-reference
docs/add-demo-notebook
```

### Refactor

```bash
refactor/nombre-refactor
```

Ejemplos:

```bash
refactor/bar-helpers
refactor/graph-metadata
```

---

## Flujo para desarrollar una nueva funcionalidad

### 1. Actualizar `main`

Antes de crear una rama nueva:

```bash
git checkout main
git pull origin main
```

---

### 2. Crear una rama de trabajo

```bash
git checkout -b feature/nombre-funcionalidad
```

Ejemplo:

```bash
git checkout -b feature/bar-negative-labels
```

---

### 3. Implementar el cambio

Modificar los archivos necesarios del paquete.

Ejemplo:

```text
helpers_ps/Grafico/graf.py
```

Si el cambio afecta una función pública como:

```python
graph_line()
graph_bar()
graph_pie()
graph_box_whiskers()
```

también debe actualizarse la documentación correspondiente.

---

### 4. Actualizar documentación

Si la funcionalidad cambia la forma de usar el paquete, actualizar como mínimo:

```text
docs/quick_reference.md
CHANGELOG.md
```

Además, según el módulo afectado:

```text
docs/graph_line.md
docs/graph_bar.md
docs/graph_pie.md
docs/graph_box_whiskers.md
Demo_Graphs.ipynb
```

Ejemplo:

Si se modifica `graph_bar()`, actualizar:

```text
docs/graph_bar.md
docs/quick_reference.md
Demo_Graphs.ipynb
CHANGELOG.md
```

---

### 5. Probar localmente

Antes de abrir un Pull Request, correr:

```bash
mkdocs build --clean
```

También validar que el paquete se pueda importar:

```bash
python -c "from helpers_ps.Grafico.graf import Graph_mtplt; print(Graph_mtplt)"
```

Si se modifican ejemplos o notebooks, validar que funcionen correctamente.

---

### 6. Hacer commit

Usar mensajes claros y descriptivos.

Formato recomendado:

```bash
git commit -m "tipo: descripción corta"
```

Tipos sugeridos:

```text
feat: nueva funcionalidad
fix: corrección de bug
docs: cambios de documentación
refactor: refactor sin cambio funcional
chore: mantenimiento
```

Ejemplos:

```bash
git commit -m "feat: add stacked bar total labels"
git commit -m "fix: avoid duplicated legend labels"
git commit -m "docs: update graph bar examples"
```

---

### 7. Subir la rama

```bash
git push origin feature/nombre-funcionalidad
```

Ejemplo:

```bash
git push origin feature/bar-negative-labels
```

---

### 8. Crear Pull Request

En GitHub:

```text
Compare & pull request
```

Configurar:

```text
base: main
compare: feature/nombre-funcionalidad
```

El Pull Request debe explicar claramente:

- qué se cambió;
- por qué se cambió;
- qué funciones afecta;
- qué pruebas se realizaron;
- qué documentación se actualizó.

---

## Template recomendado para Pull Requests

Cada Pull Request debe incluir:

```markdown
## Descripción

Describir brevemente el cambio realizado.

## Tipo de cambio

- [ ] Nueva funcionalidad
- [ ] Corrección de bug
- [ ] Refactor
- [ ] Documentación
- [ ] Mantenimiento

## Archivos principales modificados

- 

## Impacto en usuarios

Describir si cambia la forma de usar alguna función pública.

## Pruebas realizadas

- [ ] Probé el cambio localmente
- [ ] Ejecuté `mkdocs build --clean`
- [ ] Validé que los ejemplos funcionan
- [ ] No rompe funcionalidad existente

## Documentación

- [ ] Actualicé `docs/`
- [ ] Actualicé `Demo_Graphs.ipynb`
- [ ] Actualicé `CHANGELOG.md`
- [ ] No aplica

## Checklist para reviewer

- [ ] El cambio es claro
- [ ] El código mantiene consistencia con el paquete
- [ ] La documentación está actualizada
- [ ] No hay datos sensibles ni credenciales
```

---

## Revisión y aprobación

Este repositorio utiliza `CODEOWNERS`.

Los siguientes archivos y carpetas requieren revisión del maintainer principal:

```text
helpers_ps/Grafico/*
docs/*
Demo_Graphs.ipynb
README.md
mkdocs.yml
CHANGELOG.md
```

Si un Pull Request modifica alguno de esos archivos, GitHub solicitará automáticamente revisión del code owner.

El Pull Request no debe mergearse hasta recibir aprobación.

---

## Merge a main

El método recomendado de merge es:

```text
Squash and merge
```

Esto mantiene el historial de `main` limpio y evita commits intermedios como:

```text
fix typo
try again
final
final final
```

El mensaje final del merge debe ser claro:

```text
feat: add stacked bar total labels
```

o

```text
fix: avoid duplicated legend labels
```

---

## Actualización automática de documentación

Cada vez que un cambio llega a `main`, GitHub Actions ejecuta el workflow de documentación.

El workflow:

1. instala las dependencias;
2. construye la documentación con MkDocs;
3. publica la documentación en GitHub Pages.

Por lo tanto, cualquier cambio en:

```text
docs/
mkdocs.yml
api_reference.md
```

se verá reflejado automáticamente en la página de documentación después del merge a `main`.

---

## Política para cambios de API pública

Cuando se modifique una función pública, se debe actualizar la documentación.

Funciones públicas principales:

```python
graph_line()
graph_bar()
graph_pie()
graph_box_whiskers()
plot()
show()
save()
```

Ejemplo:

Si se agrega un nuevo parámetro a:

```python
graph_bar()
```

se debe actualizar:

```text
docs/graph_bar.md
docs/quick_reference.md
Demo_Graphs.ipynb
CHANGELOG.md
```

---

## Política para el maintainer principal

El maintainer principal puede hacer push directo a `main` únicamente para:

- correcciones menores;
- cambios urgentes;
- ajustes de documentación simples;
- mantenimiento operativo del repositorio.

Para cambios grandes o nuevas funcionalidades relevantes, se recomienda que incluso el maintainer utilice una rama y Pull Request para mantener trazabilidad.

---

## Resumen del flujo

```text
main
│
├── feature/nueva-funcionalidad
│       ↓
│   cambios en código
│       ↓
│   actualización de docs / ejemplos / changelog
│       ↓
│   pruebas locales
│       ↓
│   push de branch
│       ↓
│   Pull Request
│       ↓
│   revisión del code owner
│       ↓
│   aprobación
│       ↓
└── squash & merge a main
        ↓
    GitHub Actions
        ↓
    GitHub Pages actualizado
```

---

## Comandos rápidos

```bash
git checkout main
git pull origin main

git checkout -b feature/nombre-cambio

# modificar código

mkdocs build --clean

git add .
git commit -m "feat: descripción corta"

git push origin feature/nombre-cambio
```

Luego abrir Pull Request en GitHub.
