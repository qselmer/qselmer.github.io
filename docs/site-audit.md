# Auditoría integral del sitio

Fecha de reaplicación: 2026-08-02  
Rama: `codex/site-audit-cleanup`  
Base inspeccionada: `master` en `f0ba367`

## Resumen ejecutivo

El sitio conserva correctamente las colecciones académicas y sus URL públicas, pero la presentación acumuló capas de personalización que compiten entre sí. La cabecera carga 17 hojas CSS adicionales a `main.css`; `assets/css/` contiene 22 archivos y las hojas personalizadas acumulan 998 usos de `!important`. La cascada resultante duplica reglas de tipografía, navegación, sidebar, tarjetas y responsive.

También se identificaron un tema oscuro que no forma parte del diseño requerido, animaciones decorativas globales, una barra lateral sticky con scroll interno, carga duplicada de Mermaid/MathJax, controles sin estado ARIA y páginas demo todavía visibles. Estas capas explican el overflow, los contrastes inconsistentes y la fragilidad de la navegación móvil.

La limpieza propuesta mantiene íntegros los registros reales y separa estrictamente Publications de Conferences. ORCID seguirá siendo una fuente externa de metadatos, no una segunda lista de publicaciones. No se reclasificará automáticamente el registro de conferencia de 2022.

## Inventario de arquitectura

| Área | Estado inicial | Decisión segura |
| --- | ---: | --- |
| `assets/css/` | 22 archivos | Consolidar en 10 archivos públicos, incluidos `main.scss` y Academicons |
| CSS personalizado enlazado | 17 archivos | Sustituir por cuatro capas globales y cuatro hojas específicas |
| `!important` personalizado | 998 usos | Eliminar mediante orden y especificidad predecibles |
| `_pages/` | 29 archivos | Conservar URL; redirigir demos sin contenido académico |
| `_layouts/` | 10 archivos | Retirar layouts no usados y corregir HTML semántico |
| `_publications/` | 2 registros | Conservar sin mezclar con conferencias |
| `_talks/` | 2 registros | Conservar como Conferences |
| `_projects/` | 6 registros | Conservar |
| `_software/` | 3 registros | Conservar |
| `_posts/` | 1 registro | Conservar y habilitar MathJax solo donde se usa |
| `images/` | 21 archivos | Optimizar PNG sin pérdida y retirar solo demos no referenciadas |
| workflows | 3 | Conservar; la limpieza no cambia automatizaciones científicas |

## Hallazgos

### CSS y layout

- `_includes/head.html` enlaza 17 hojas personalizadas después de `main.css`.
- Varias hojas redefinen los mismos selectores de navegación, sidebar y contenido.
- Las reglas `!important` se usan como mecanismo general de precedencia.
- El sidebar combina `position: sticky`, altura máxima y `overflow-y`, produciendo scroll interno.
- Existen reglas de tema oscuro, fondos marinos animados y transiciones de entrada globales.
- La navegación greedy debe conservar una lista medible (`display: table`) para mover enlaces sin provocar overflow.

### JavaScript

- `theme.js` y `_main.js` duplican responsabilidades del tema.
- Plotly cambia de plantilla según tema aunque el diseño final será claro.
- Mermaid se inicializa más de una vez.
- MathJax se carga globalmente aunque solo una entrada lo necesita.
- Los botones del menú y del perfil no comunican `aria-expanded`/`aria-hidden`.

### Semántica y accesibilidad

- Hay botones sin nombre accesible y controles sin `aria-controls`.
- Algunas plantillas generan párrafos anidados o sin cerrar.
- Varias páginas mezclan Markdown literal dentro de bloques HTML.
- Imágenes de archivo y presentaciones necesitan alternativas descriptivas y dimensiones.
- Los estilos inline de citas deben convertirse en una clase reutilizable.

### Contenido y URL

- Las páginas de demostración (`/markdown/`, `/page-archive/`, `/collection-archive/`, `/archive-layout-with-content/` y `/non-menu-page/`) no deben quedar visibles, pero sus URL se conservarán como redirecciones.
- `/portfolio/` ya representa una URL histórica y debe redirigir a `/projects/`.
- Publications y Conferences permanecerán en páginas y colecciones distintas.
- Contact y Newsletter permanecerán desactivados, con alternativas de correo y RSS.
- Los enlaces directos antiguos de PICES requieren sustituirse por la página oficial estable, sin inventar recursos.

## Arquitectura CSS objetivo

1. `main.scss`: estilos base del tema y proveedores.
2. `site-base.css`: tokens, tipografía, foco, medios y tablas.
3. `site-layout.css`: masthead, contenedor, sidebar estático y footer.
4. `site-components.css`: botones, tarjetas, archivos, formularios y utilidades.
5. `site-responsive.css`: navegación y breakpoints.
6. `page-specific/home.css`.
7. `page-specific/publications.css`.
8. `page-specific/research.css`.
9. `page-specific/data.css`.
10. `academicons.css`.

Las hojas específicas se cargarán condicionalmente según `page.url`. No se mantendrán tema oscuro, partículas, fondos animados ni animaciones de entrada.

## Validación prevista

- `npm test` para sintaxis y bundle JavaScript.
- `bundle install` y `bundle exec jekyll build`.
- Validador del HTML generado para enlaces internos, `alt`, nombres de botones e IDs duplicados.
- Inspección responsive para evitar overflow horizontal, scroll interno del sidebar, contenido demo y contraste blanco sobre blanco.
- `git diff --check`, estado limpio y comparación final contra `master`.

## Límites editoriales

La auditoría no elimina ni inventa publicaciones, proyectos, presentaciones, datos o software. Cualquier reclasificación científica queda fuera de esta limpieza técnica. En particular, el registro de conferencia de 2022 permanecerá en su clasificación actual hasta una decisión editorial explícita.
