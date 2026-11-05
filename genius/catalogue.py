"""Deterministic, inspectable GENIUS-5000 research-profile catalogue.

These records prescribe bounded research work. They do not certify a model's
scientific ability. Registry integrity is tested separately from that ability.
The scientific taxonomy is maintained here; generated JSON never changes it.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

VERSION = "1.0.0"
DIVISION_COUNTS = {
    "rg": 500, "lqg": 500, "strings": 450, "twistors": 650,
    "topology": 550, "algebraic_geometry": 550, "qft": 500,
    "categories": 350, "computation": 500, "integration": 450,
}
DIVISION_NAMES = {
    "rg": "Relatividad general y geometría gravitatoria",
    "lqg": "Gravedad cuántica de bucles y espumas de espín",
    "strings": "Teoría de cuerdas, supergravedad y teoría M",
    "twistors": "Teoría de twistores y problema de Googly",
    "topology": "Topología algebraica y teoría de homotopía",
    "algebraic_geometry": "Geometría algebraica y geometría derivada",
    "qft": "Teoría cuántica de campos y teorías gauge",
    "categories": "Categorías superiores y geometría no conmutativa",
    "computation": "Verificación formal, análisis numérico y computación científica",
    "integration": "Integración científica, arbitraje y revisión crítica",
}

COMMON_CORE = [
    "álgebra lineal y multilineal", "análisis y ecuaciones diferenciales",
    "geometría diferencial", "fundamentos de topología",
    "mecánica clásica y formulación variacional", "relatividad y teoría cuántica",
    "lectura de demostraciones y literatura científica", "reproducibilidad computacional",
]

# The referents identify methods, not impersonations or measured equivalence.
ARCHETYPES = {
    "einstein": {
        "name": "Albert Einstein", "method": "principios físicos y experimentos mentales",
        "observable": "enunciar principios y calcular un límite de correspondencia",
        "reference": "https://www.nobelprize.org/prizes/physics/1921/einstein/biographical/",
    },
    "hawking": {
        "name": "Stephen Hawking", "method": "geometría global y aproximación semiclásica",
        "observable": "declarar causalidad, horizontes y el control de la aproximación",
        "reference": "https://www.cam.ac.uk/stories/stephen-hawking",
    },
    "newman": {
        "name": "Ezra Ted Newman", "method": "espinores y tétradas nulas",
        "observable": "fijar normalización nula y comprobar identidades espinoriales",
        "reference": "https://www.physicsandastronomy.pitt.edu/ted-newman",
    },
    "von-neumann": {
        "name": "John von Neumann", "method": "estructuras operatoriales y algoritmos",
        "observable": "especificar dominio de operadores y un procedimiento comprobable",
        "reference": "https://www.ias.edu/von-neumann",
    },
    "penrose": {
        "name": "Roger Penrose", "method": "geometría conforme y correspondencias",
        "observable": "escribir mapas, condiciones de integrabilidad y reconstrucción",
        "reference": None,
    },
    "noether": {
        "name": "Emmy Noether", "method": "simetrías e invariantes",
        "observable": "derivar una identidad de simetría con hipótesis explícitas",
        "reference": None,
    },
    "dirac": {
        "name": "Paul Dirac", "method": "operadores y restricciones",
        "observable": "contar restricciones y grados de libertad físicos",
        "reference": None,
    },
    "feynman": {
        "name": "Richard Feynman", "method": "representaciones y modelos calculables",
        "observable": "calcular un ejemplo y contrastarlo mediante otra representación",
        "reference": None,
    },
    "grothendieck": {
        "name": "Alexander Grothendieck", "method": "functorialidad y espacios de módulos",
        "observable": "definir objetos, morfismos y propiedad universal pertinentes",
        "reference": None,
    },
    "riemann": {
        "name": "Bernhard Riemann", "method": "geometría y análisis",
        "observable": "relacionar un invariante geométrico con un cálculo local",
        "reference": None,
    },
    "weyl": {
        "name": "Hermann Weyl", "method": "grupos, espinores y conexiones gauge",
        "observable": "identificar representaciones y comprobar covariancia",
        "reference": None,
    },
    "poincare": {
        "name": "Henri Poincaré", "method": "topología, estabilidad y dinámica cualitativa",
        "observable": "localizar una obstrucción global o un criterio de estabilidad",
        "reference": None,
    },
}

QUALITY_TARGETS = [
    {"id": "physical-imagination", "quality": "imaginación física",
     "behavior": "formular un modelo mínimo con variables, observables y simetrías; delimitar cuándo no hay interpretación física",
     "deliverable": "problema preciso y ejemplo calculable", "acceptance": "el ejemplo distingue al menos dos hipótesis o elimina una ambigüedad"},
    {"id": "mathematical-depth", "quality": "profundidad matemática",
     "behavior": "definir objetos, dominios e hipótesis y enumerar dependencias del argumento",
     "deliverable": "enunciado y argumento auditable", "acceptance": "cada uso de un resultado previo identifica sus hipótesis"},
    {"id": "disciplined-creativity", "quality": "creatividad disciplinada",
     "behavior": "proponer una ruta alternativa y una prueba concreta capaz de descartarla",
     "deliverable": "comparación de rutas y primer cálculo", "acceptance": "la propuesta incluye un criterio de fracaso verificable"},
    {"id": "critical-capacity", "quality": "capacidad crítica",
     "behavior": "buscar un contraejemplo, un caso degenerado y una posible circularidad",
     "deliverable": "registro de intentos de refutación", "acceptance": "los casos ensayados y su alcance constan, incluso si no refutan"},
    {"id": "academic-maturity", "quality": "madurez académica",
     "behavior": "atribuir fuentes, guardar cálculos reproducibles y expresar lagunas",
     "deliverable": "informe con archivos, referencias y colaboración necesaria",
     "acceptance": "las fuentes consultadas y las pendientes están separadas; no hay credenciales inventadas"},
]

# Each row is one actual research line: specialty | object | bounded problem |
# method | regime. All 100 lines are inspected rather than produced by an LLM
# at runtime. A line is expanded through bounded modes and distinct audit tasks.
_TRACK_ROWS = {
    "rg": [
        "Problema de Cauchy de Einstein|datos (h,K) sobre una hipersuperficie espacial|propagación de restricciones y unicidad módulo difeomorfismos|reducción hiperbólica y estimaciones de energía|lorentziano local con regularidad Sobolev declarada",
        "Gravedad de primer orden|co-tétrada invertible y conexión de Lorentz|comparar variaciones Palatini y métrica y localizar el papel de la torsión|cálculo exterior y eliminación de auxiliares|cuatro dimensiones, conexión independiente y contorno fijado",
        "Formalismo Newman–Penrose|tétrada nula y coeficientes de espín|reconstruir una identidad de curvatura verificando la normalización|cálculo espinorial y ecuaciones NP|lorentziano local; no extrapolar a tétradas degeneradas",
        "Geometría conforme de Einstein|métrica y compactificación conforme|controlar pesos y regularidad de datos en el infinito conforme|ecuaciones conformes y análisis de frontera|clase asintótica y función definidora explícitas",
        "Causalidad global|espacio-tiempo globalmente hiperbólico|separar existencia de hipersuperficies de Cauchy y completitud geodésica|geometría causal y construcción de ejemplos|lorentziano global con condiciones causales declaradas",
        "Horizontes y termodinámica|horizonte de Killing y cargas de frontera|comparar variaciones de área y carga sin confundir identidad y interpretación térmica|espacio de fases covariante|horizonte estacionario y perturbación de primer orden",
        "Gravedad canónica ADM|espacio de fases de métricas y momentos|verificar cierre del álgebra de restricciones y conteo físico|corchetes de Poisson y análisis de Dirac|foliación espacial y condiciones de frontera explícitas",
        "Estabilidad gravitatoria|perturbación de una solución de Einstein|distinguir modos gauge de inestabilidades físicas|análisis espectral y estimaciones de energía|perturbativo sobre fondo especificado",
        "Relatividad asintótica|datos nulos y simetrías asintóticas|fijar cargas y flujos con condiciones de caída verificables|expansión asintótica y simetrías BMS|infinito nulo; órdenes de expansión declarados",
        "Soluciones exactas y Petrov|tensor de Weyl y congruencias nulas|clasificar un ansatz y comprobar las ecuaciones de Einstein|invariantes de curvatura y clasificación algebraica|soluciones locales; globalidad requiere prueba separada",
    ],
    "lqg": [
        "Holonomías y flujos|álgebra de holonomías-flujos sobre un grafo|fijar dominio y representación sin atribuir dinámica a la cinemática|análisis de representaciones y corchetes|grafo finito y grupo compacto declarados",
        "Redes de espín|intertwiners SU(2) y estados de grafo|contar el subespacio invariante y sus redundancias|teoría de representaciones y recoupling|grafo fijo con espines finitos",
        "Geometría cuántica|operadores de área y volumen|comparar regularizaciones y dominios de operadores geométricos|análisis espectral de matrices de intertwiners|truncación finita; espectro no implica dinámica continua",
        "Restricción hamiltoniana|operador regularizado y estados cilíndricos|comprobar el alcance del álgebra de restricciones|análisis de regularización y comparación de conmutadores|regulador y dominio de operadores explícitos",
        "Espumas EPRL/FK|amplitud de un complejo celular etiquetado|verificar mapas de simplicidad y normalizaciones de una amplitud|integrales de grupo y teoría de representaciones|complejo fijo y firma especificada",
        "Límite asintótico de espumas|amplitud de vértice y datos de frontera coherentes|identificar puntos críticos y sectores degenerados|fase estacionaria y análisis de Hessiano|gran espín; hipótesis de no degeneración explícitas",
        "Refinamiento y coarse graining|familia de amplitudes en complejos relacionados|definir mapas de refinamiento y comprobar compatibilidad|renormalización discreta y tensores|familia finita de refinamientos; continuo pendiente",
        "Cosmología cuántica de bucles|restricción de un modelo homogéneo|auditar elección de reloj y dominio de validez efectivo|ecuaciones en diferencias y dinámica relacional|minisuperspace; no inferir validez en teoría completa",
        "Group field theory|campo sobre productos de grupos|identificar qué combinatoria produce caras, aristas y vértices|expansión diagramática y teoría de grupos|truncación y orden diagramático especificados",
        "Fronteras y horizontes LQG|estados de frontera y restricciones de horizonte|auditar conteo de estados y dependencia del ensamble|combinatoria exacta y restricciones gauge|área y condiciones de horizonte declaradas",
    ],
    "strings": [
        "Sigma modelos de cuerdas|acción de sigma modelo bidimensional|distinguir invariancia clásica y condiciones cuánticas sobre el fondo|grupo de renormalización y funciones beta|expansión en alpha prima y orden de lazo explícitos",
        "Cuantización BRST de cuerdas|complejo BRST de estados|comparar cohomología física con estados espurios|álgebra de operadores y cohomología|fondo y carga central declarados",
        "Supergravedad|campos y transformaciones locales supersimétricas|verificar cierre y consistencia de una truncación|variación de la acción y álgebra de supersimetría|dimensión y orden fermiónico fijados",
        "Compactificaciones y módulos|variedad interna y campos de módulos|contar deformaciones e identificar supuestos de estabilización|cohomología y teoría efectiva|régimen de volumen y acoplamiento declarado",
        "D-branas y cargas|condiciones de borde y clases de carga|separar clasificación topológica de estabilidad dinámica|teoría K y análisis de frontera|fondo, torsión y anomalías explícitos",
        "Dualidades de cuerdas|dos descripciones con parámetros identificados|construir el diccionario de un observable protegido|comparación de espectros y funciones de partición|sector protegido o régimen perturbativo especificado",
        "Holografía AdS/CFT|fuentes de frontera y campos del bulk|comparar un correlador con normalizaciones y contraterminos|renormalización holográfica|gran N, acoplamiento y orden de expansión declarados",
        "Flujos y anomalías|campos de flujo y cociclos de anomalía|comprobar cuantización y condiciones globales de consistencia|cohomología diferencial y descenso|topología y contenido de campos fijados",
        "Sectores de teoría M|C-field y datos de branas|comparar propuestas de cuantización de carga sin asumir equivalencias generales|cohomología y análisis de modelos límite|sector especificado; formulación completa no presupuesta",
    ],
    "twistors": [
        "Correspondencia no lineal del gravitón|tres-variedad twistoriana con líneas racionales|precisar hipótesis de reconstrucción de un espacio-tiempo ASD|deformación de curvas y doble fibración|complejo analítico local, normal O(1)+O(1)",
        "Transformada de Penrose lineal|clases de cohomología de haces sobre un dominio twistoriano|comprobar peso y helicidad de un campo sin masa|transformada integral y cohomología de Cech|dominio y condiciones de contorno explícitos",
        "Problema de Googly no lineal|deformación de datos twistoriales fuera del sector ASD|formular qué segunda helicidad debe recuperarse y dónde aparece una obstrucción|teoría de deformaciones y reconstrucción|local o formal por orden declarado; googly general abierto",
        "Geometría ambitwistoriana|espacio de geodésicas nulas complejificadas|fijar incidencia y condiciones de reconstrucción|geometría de contacto y doble fibración|analítico local y dimensión declarada",
        "Realidad twistorial|involución antilineal y líneas reales|distinguir firmas y componentes de realidad|geometría real y espinores|euclídeo, lorentziano o split declarados sin intercambio silencioso",
        "Acciones twistoriales gravitatorias|campos de Dolbeault y acción sobre espacio twistor|separar equivalencia perturbativa de reconstrucción no lineal|variación funcional y fijación gauge|orden perturbativo y pesos homogéneos explícitos",
        "Gravitación con constante cosmológica|estructura de contacto o Poisson twistoriana|comparar el límite Lambda hacia cero sin perder rango|geometría de contacto y degeneración controlada|complejo local con Lambda y escala fijados",
        "Haces y ecuaciones de Ward|fibrado holomorfo trivial en líneas|verificar correspondencia con un sector Yang–Mills|desdoblamiento holomorfo y conexión inducida|sector ASD y condiciones de trivialidad explícitos",
        "Deformaciones L infinito twistoriales|complejo diferencial graduado de deformaciones|separar Maurer–Cartan formal de equivalencia física|álgebra homotópica y obstrucciones|formal por orden; completación y gauge declarados",
        "Obstrucciones globales twistoriales|familia global de curvas racionales|localizar dónde falla extensión global de una correspondencia local|cohomología de haces y descenso|topología, cobertura y condiciones de separación fijadas",
        "Twistores y amplitudes|datos de espín-helicidad y representante cohomológico|contrastar helicidades y pesos de una amplitud concreta|factorización y transformadas twistoriales|árbol o lazos y multiplicidad especificados",
        "Geometría CR y datos nulos|estructura CR y congruencia nula|relacionar integrabilidad CR y ecuaciones espinoriales|geometría CR y formalismo Newman–Penrose|regularidad y realidad lorentziana declaradas",
        "Espacios de módulos de líneas|espacio de deformaciones de una línea twistoriana|distinguir deformación abstracta y métrica reconstruible|teoría de Kodaira y sucesiones exactas|vecindad de una curva compacta con normal declarado",
    ],
    "topology": [
        "Teoría de obstrucciones|torre de Postnikov de una aplicación|localizar la primera obstrucción a extender una sección|cohomología con sistemas locales|complejos CW y rango de dimensiones fijados",
        "Clases características|fibrado principal sobre un complejo finito|comparar obstrucciones de levantamiento y clases características|espacios clasificantes y operaciones cohomológicas|grupo, coeficientes y dimensión declarados",
        "Teoría K topológica|clases de fibrados complejos o reales|calcular un grupo K y distinguir torsión de rango|periodicidad de Bott y sucesiones exactas|espacio compacto de tipo CW finito",
        "Bordismo y anomalías|grupo de bordismo con estructura tangencial|separar clasificación topológica de realización de una QFT|sucesión espectral de Atiyah–Hirzebruch|estructura tangencial y dimensión explícitas",
        "Homotopía estable|espectro y sus grupos de homotopía|controlar el rango de estabilidad de un cálculo|sucesiones espectrales y secuencias cofibra|grado y localización fijados",
        "Homotopía racional|modelo diferencial graduado de un espacio|comparar información racional con torsión perdida|modelos de Sullivan y complejos de Chevalley–Eilenberg|nilpotencia y tipo finito explícitos",
        "Homotopía cromática|espectro localizado a altura dada|delimitar qué detecta una teoría de cohomología|localización y sucesiones espectrales|primo, altura y grado fijados",
        "Cohomología diferencial|cociclos diferenciales y curvatura|comparar cuantización integral, forma diferencial y holonomía|sucesiones exactas de cohomología diferencial|variedad suave y normalización integral explícitas",
        "Teoría de nudos y enlaces|complemento de un enlace y representaciones|comparar un invariante con la información topológica que conserva|grupos fundamentales e invariantes de enlaces|enlace orientado y normalizaciones declaradas",
        "Topología simpléctica y Floer|complejo de Floer de un sistema no degenerado|verificar compactitud y dependencia de elecciones auxiliares|teoría de Fredholm y análisis de módulos|hipótesis monotónicas o exactas declaradas",
        "Cohomología elíptica y tmf|espectro de cohomología y orientación|distinguir formas modulares ordinarias de información homotópica|orientaciones y secuencias espectrales|estructura tangencial, primo y grado declarados",
    ],
    "algebraic_geometry": [
        "Cohomología de haces|haz coherente sobre un esquema|calcular un grupo de cohomología con hipótesis de finitud|resoluciones y complejos de Cech|base noetheriana y cobertura explícitas",
        "Deformaciones de esquemas|complejo cotangente de un esquema|identificar espacios tangentes y obstrucciones sin confundirlos|Ext y complejo cotangente|anillos artinianos y característica declarados",
        "Espacios de módulos|problema de módulos con automorfismos|distinguir espacio grueso y stack que conserva estabilizadores|functores de puntos y descenso|topología de Grothendieck y condiciones de finitud fijadas",
        "Geometría algebraica derivada|intersección derivada de subesquemas|comparar Tor superior y la intersección clásica|álgebra diferencial graduada y producto derivado|característica cero o modelo superior explícito",
        "Categorías derivadas coherentes|categoría derivada de haces coherentes|verificar alcance de un funtor Fourier–Mukai|resoluciones y kernels integrales|propiedad, suavidad y enhancement declarados",
        "Curvas y fibrados|fibrado sobre una curva algebraica|estudiar estabilidad y deformaciones bajo grado fijado|Riemann–Roch y teoría de módulos|curva suave proyectiva y polarización declarada",
        "Geometría compleja y GAGA|espacio algebraico y analitificación|determinar cuándo una construcción analítica admite comparación algebraica|comparación de haces y cohomología|hipótesis de propiedad explícitas; no GAGA indiscriminado",
        "Singularidades|álgebra local y deformación de singularidad|calcular invariantes que detecten suavizado u obstrucción|álgebra conmutativa y resoluciones|dimensión, base y completación fijadas",
        "Geometría simpléctica derivada|stack con forma simpléctica desplazada|auditar grado de la forma y no degeneración derivada|complejo tangente y dualidad|tipo de stack y desplazamiento declarados",
        "Simetría espejo homológica|dos categorías con estructuras de composición|precisar categorías comparadas y datos necesarios para equivalencia|funtores A infinito y comparación de generadores|caso y coeficientes fijados; conjetura general no presupuesta",
        "Geometría proyectiva twistoriana|curvas y fibrados normales en una variedad proyectiva|separar construcción algebraica y reconstrucción analítica de métricas|sucesiones de haces y deformación de curvas|curvas racionales sobre C con normal declarado",
    ],
    "qft": [
        "QFT perturbativa renormalizada|funcionales y contraterminos locales|auditar dependencia del esquema y del regulador|renormalización y análisis dimensional|orden de lazo y escala declarados",
        "Teorías gauge BRST/BV|complejo BV de campos y antifields|verificar ecuación maestra y cierre gauge|cohomología local y corchete antibracket|clásico o cuántico y regularización explícitos",
        "Anomalías locales|variación efectiva y cociclo de anomalía|comparar descenso y cancelación por contenido de campos|cohomología BRST y descenso|dimensión y representaciones declaradas",
        "Anomalías globales|familia de operadores de Dirac|separar anomalía perturbativa de obstrucción global|índice de familias y bordismo|estructura de espín y grupo gauge fijados",
        "Amplitudes y factorización|amplitud de dispersión con helicidades|comprobar residuos, unitariedad y conteo de dimensiones|espín-helicidad y cortes generalizados|orden perturbativo y estados externos explícitos",
        "QFT en espacio-tiempo curvo|álgebra de campos y estado Hadamard|comparar renormalización local y elección de estado|análisis microlocal y point splitting|fondo globalmente hiperbólico y regularidad fijada",
        "Teoría algebraica de campos|red de álgebras locales|distinguir localidad, isotonicidad y elección de representación|álgebras de operadores y estados|regiones y categoría de espacios-tiempo declaradas",
        "Teorías conformes|álgebra de operadores y correladores|controlar convergencia y restricciones del bootstrap|OPE y bloques conformes|dimensión, espectro y supuestos unitarios declarados",
        "Simetrías generalizadas|defectos y operadores extendidos|definir fusión y detectar anomalías de una simetría|álgebra de defectos y cohomología|dimensión, codimensión y condiciones de borde fijadas",
        "Teorías efectivas de unificación|acción efectiva de gravedad, gauge y materia|separar suma de sectores y mecanismo físico de unificación|matching y expansión de operadores|escala de corte y orden efectivo explícitos",
    ],
    "categories": [
        "Categorías superiores estables|categoría infinito estable y categoría homotópica|determinar qué coherencias se pierden al truncar|límites homotópicos y localización|universo y condiciones de presentabilidad declarados",
        "TQFT extendida|funtor monoidal desde una categoría de bordismos|delimitar dualizabilidad y datos de tangencia necesarios|dualidad categórica y composición de bordismos|dimensión y nivel de extensión fijados",
        "Geometría no conmutativa espectral|triple espectral con operador de Dirac|auditar dominio, compactitud del resolvente y contenido geométrico|análisis espectral y álgebras de operadores|álgebra y dominio densamente definido explícitos",
        "Teoría de Morita|álgebras y categorías de módulos|separar equivalencia de Morita de isomorfismo de álgebras|bimódulos y productos tensoriales|categoría y condiciones de finitud declaradas",
        "Álgebra homotópica|álgebra L infinito y ecuación de Maurer–Cartan|comparar deformaciones y equivalencia gauge en rango controlado|filtraciones y transferencia homotópica|nilpotencia o completación explícitas",
        "Categorías tensoriales|categoría monoidal y objetos duales|verificar compatibilidad de trenza, asociador y trazas|coherencia monoidal y diagramas conmutativos|base, rigidez y semisimplicidad declaradas",
        "Cuantización por deformación|álgebra deformada de observables de Poisson|verificar asociatividad al orden calculado|cohomología de Hochschild y productos estrella|serie formal en hbar; convergencia no presupuesta",
    ],
    "computation": [
        "Formalización Lean|enunciado formal y dependencias de Mathlib|comparar teorema informal y término comprobado por el kernel|formalización y type checking|versión fijada y ausencia de axiomas añadidos documentada",
        "Formalización Coq|definiciones y término de prueba|separar comprobación del kernel y corrección de la traducción|asistentes de prueba y extracción|versión y axiomas usados explícitos",
        "Álgebra simbólica exacta|expresiones racionales y polinomiales|verificar identidades preservando dominios y denominadores|formas normales y aritmética exacta|anillo, variables y localización declarados",
        "Álgebra computacional|ideal polinomial y módulo finitamente presentado|comprobar pertenencia, dimensión o resolución con certificados|bases de Groebner y sizigias|orden monomial y cuerpo exacto declarados",
        "Geometría diferencial computacional|métrica y expresiones tensoriales|recalcular curvatura y auditar índices y signos|diferenciación simbólica y contracción tensorial|carta y rango regular de coordenadas fijados",
        "PDE numéricas gravitatorias|discretización de ecuaciones y restricciones|medir convergencia y deriva de restricciones|diferencias finitas y refinamiento de malla|dominio, estabilidad CFL y condiciones de frontera fijados",
        "Integración y muestreo|integral regularizada y estimador|separar error de muestreo, sesgo y error de modelo|cuadratura y Monte Carlo con semilla|regulador, tolerancia y tamaño de muestra explícitos",
        "Análisis espectral numérico|matriz truncada de un operador|comprobar dependencia de truncación y residuos espectrales|diagonalización y cotas de residuos|dominio del operador y tamaño de truncación declarados",
        "Topología computacional|complejo simplicial y mapas de cadenas|comparar homología exacta con inferencia de datos|reducción de matrices y certificados de cadenas|complejo, coeficientes y filtración declarados",
        "Reproducibilidad científica|código, datos y manifiesto de ejecución|reconstruir resultados desde entradas versionadas|pruebas de regresión y huellas de archivos|entorno y tolerancias fijados; simulación etiquetada",
    ],
    "integration": [
        "Formulación de problemas|pregunta científica y condiciones de éxito|transformar una intuición en un enunciado refutable|análisis de supuestos y diseño de modelo mínimo|alcance científico declarado sin resolver por terminología",
        "Auditoría de demostraciones|enunciado, argumento y grafo de lemas|reconstruir el paso decisivo y detectar circularidad|revisión separada y búsqueda de contraejemplos|hipótesis exactas; revisión interna identificada",
        "Auditoría física|acción, restricciones y observables|comprobar unidades, signos, gauge y grados de libertad|análisis dimensional y conteo de restricciones|firma y régimen físico declarados",
        "Revisión bibliográfica|fuentes primarias y afirmaciones atribuidas|verificar qué resultado respalda cada referencia|búsqueda trazable y lectura de hipótesis|fecha, versión y alcance de búsqueda explícitos",
        "Comparación Claude–Codex|informes de ejecuciones con contexto separado|registrar acuerdos, desacuerdos y pruebas resolutivas|reconstrucción cruzada y matriz de afirmaciones|separación de ejecución no garantiza independencia de errores",
        "Integración entre programas|resultados de gravedad, unificación y googly|construir mapas explícitos sin asumir una teoría común|comparación de objetos, observables y regímenes|solo transferir resultados que conservan las hipótesis",
        "Memoria de investigación|registro de afirmaciones y dependencias|propagar cambios y conservar refutaciones con evidencia|versionado y validación de grafos|trazabilidad de archivos y revisiones internas/externas separada",
        "Escritura científica|argumento técnico y archivos reproducibles|producir un manuscrito que refleje el alcance real|edición estructural y auditoría de referencias|borrador, resultado parcial y demostración diferenciados",
        "Evaluación de capacidades|tareas benchmark y resultados observados|distinguir objetivo de diseño y competencia medida|evaluación por rúbrica y controles negativos|evidencia por ejecución; no generalizar por pertenecer al catálogo",
    ],
}

SPECIALIZED_KNOWLEDGE = {
    "rg": ["geometría lorentziana", "ecuaciones de Einstein", "espinores", "análisis hiperbólico"],
    "lqg": ["representaciones de SU(2)", "restricciones hamiltonianas", "holonomías", "amplitudes de espumas"],
    "strings": ["QFT bidimensional", "supersimetría", "geometría compleja", "teoría K"],
    "twistors": ["geometría conforme espinorial", "cohomología de haces", "teoría de deformaciones", "helicidad"],
    "topology": ["homología y cohomología", "homotopía", "sucesiones espectrales", "espacios clasificantes"],
    "algebraic_geometry": ["esquemas y haces", "álgebra conmutativa", "categorías derivadas", "complejo cotangente"],
    "qft": ["renormalización", "BRST/BV", "anomalías", "teoría de representaciones"],
    "categories": ["categorías monoidales y superiores", "álgebra homotópica", "álgebras de operadores", "deformaciones"],
    "computation": ["aritmética exacta", "análisis de error", "algoritmos", "verificación formal"],
    "integration": ["lógica de demostraciones", "consistencia física", "gestión de evidencia", "evaluación reproducible"],
}

# Modes give substantive differences of scope and method within a line.
# Their use is conditional: a global or numerical mode may legitimately yield
# an obstruction/not-applicable report instead of silently assuming existence.
MODE_SETS = {
    "physics": [
        ("local", "modelo local con fondo y regularidad fijados", "reducción local y ejemplo calculable", "SymPy"),
        ("perturbative", "variación de primer orden con parámetro pequeño declarado", "linealización y control de términos descartados", "SymPy"),
        ("global", "compatibilidad de cartas y condiciones de frontera globales", "descenso y búsqueda de obstrucciones globales", "SageMath"),
        ("finite", "truncación finita o ansatz explícito, sin inferir el continuo", "cálculo exacto en un modelo restringido", "Python-stdlib"),
        ("comparison", "dos formulaciones con dominios comparables", "diccionario explícito y comprobación por dos vías", "Python-stdlib"),
    ],
    "math": [
        ("affine-local", "cálculo local sobre un abierto o modelo celular indicado", "resolución explícita y cálculo local", "SageMath"),
        ("deformation", "familia formal o sucesión de aproximaciones finitas", "complejos de deformaciones y obstrucciones", "Macaulay2"),
        ("global-descent", "pegado global con cobertura y coeficientes declarados", "descenso y sucesiones exactas", "SageMath"),
        ("finite-example", "ejemplo finitamente presentado con generadores explícitos", "álgebra exacta y construcción de ejemplos", "SageMath"),
        ("comparison", "comparación de dos presentaciones del mismo problema", "funtores, mapas de cadenas o propiedades universales", "Lean"),
    ],
    "computing": [
        ("exact", "instancia exacta de tamaño pequeño", "certificado verificable y aritmética exacta", "Python-stdlib"),
        ("refinement", "familia de tamaños o precisiones crecientes", "estudio de convergencia y sensibilidad", "SciPy"),
        ("adversarial", "entrada degenerada o mal condicionada", "generación de casos adversos e invariantes", "Python-stdlib"),
        ("cross-tool", "misma entrada en dos implementaciones", "comparación independiente de certificados", "SageMath"),
        ("reproduction", "entorno limpio con versiones declaradas", "reproducción desde manifiesto y entradas", "Python-stdlib"),
    ],
    "integration": [
        ("scope", "un enunciado con criterio de éxito delimitado", "auditoría de alcance y supuestos", "Python-stdlib"),
        ("reconstruction", "un argumento y sus dependencias directas", "reconstrucción separada del paso decisivo", "Python-stdlib"),
        ("adversarial", "un caso negativo o desacuerdo documentado", "análisis adversarial de evidencia y contraejemplos", "Python-stdlib"),
        ("cross-program", "dos informes con convenciones comparables", "matriz de correspondencias y desacuerdos", "Python-stdlib"),
        ("reproducibility", "un paquete de archivos y referencias versionados", "reconstrucción desde fuentes y huellas", "Python-stdlib"),
    ],
}

# Each task changes the actual question and the required observable output.
TASKS = [
    ("definitions", "conceptual", "precisar objetos, dominios y la pregunta mínima", "ficha de definiciones y criterio de éxito", "tipado, dominios y ambigüedad de conceptos", "einstein"),
    ("hypotheses", "mathematics", "identificar hipótesis necesarias y ensayar retirar una", "enunciado y prueba o contraejemplo a la retirada", "hipótesis ocultas y cuantificadores", "grothendieck"),
    ("derivation", "mathematics", "reconstruir el paso técnico decisivo con dependencias", "derivación o demostración numerada", "reglas lógicas, signos y uso de resultados previos", "dirac"),
    ("example", "computation", "construir una instancia explícita y calcular un invariante", "archivo reproducible con entradas y salida", "control exacto de un ejemplo calculable", "feynman"),
    ("degeneration", "counterexample", "buscar un caso degenerado que vulnere una generalización", "contraejemplo u obstáculo con alcance declarado", "límites singulares, rango y casos excluidos", "poincare"),
    ("symmetry", "physics", "comprobar qué simetrías y redundancias preserva la construcción", "tabla de invariantes, gauge o equivalencias pertinentes", "covariancia, redundancias y grados de libertad cuando apliquen", "noether"),
    ("dependencies", "audit", "revisar fuentes y detectar una dependencia circular o inestable", "grafo de dependencias y localizadores de fuentes", "circularidad, atribución y cambio de hipótesis", "von-neumann"),
    ("refutation", "counterexample", "formular un test independiente capaz de refutar el enunciado", "registro de intentos de refutación y resultado", "refutabilidad y cobertura de casos límite", "hawking"),
    ("dictionary", "integration", "comparar una formulación alternativa mediante mapas explícitos", "diccionario con dominio, inversa o fallo de reconstrucción", "estructura preservada y alcance de la comparación", "penrose"),
    ("synthesis", "integration", "integrar evidencia y proponer el siguiente cálculo discriminante", "informe clasificado con pendientes y siguiente paso", "sobreafirmación y trazabilidad de evidencia", "weyl"),
]

PRIMARY_ARCHETYPES = {
    "rg": ["einstein", "newman", "riemann", "hawking"],
    "lqg": ["dirac", "weyl", "poincare", "feynman"],
    "strings": ["weyl", "noether", "dirac", "grothendieck"],
    "twistors": ["penrose", "newman", "grothendieck", "riemann"],
    "topology": ["poincare", "grothendieck", "riemann", "weyl"],
    "algebraic_geometry": ["grothendieck", "riemann", "weyl", "poincare"],
    "qft": ["feynman", "dirac", "noether", "von-neumann"],
    "categories": ["grothendieck", "von-neumann", "weyl", "noether"],
    "computation": ["von-neumann", "dirac", "feynman", "poincare"],
    "integration": ["noether", "einstein", "von-neumann", "poincare"],
}
PROGRAM_TAGS = {
    "rg": ["quantum_gravity", "unified_field_theory"],
    "lqg": ["quantum_gravity"], "strings": ["quantum_gravity", "unified_field_theory"],
    "twistors": ["googly", "quantum_gravity"],
    "topology": ["quantum_gravity", "unified_field_theory", "googly"],
    "algebraic_geometry": ["googly", "unified_field_theory", "quantum_gravity"],
    "qft": ["unified_field_theory", "quantum_gravity"],
    "categories": ["quantum_gravity", "unified_field_theory"],
    "computation": ["googly", "quantum_gravity", "unified_field_theory"],
    "integration": ["googly", "quantum_gravity", "unified_field_theory"],
}

REQUIRED_FIELDS = [
    "id", "version", "division", "specialty", "subspecialties", "competence_limits",
    "archetypes", "knowledge", "objects", "problems", "methods", "regime", "tools",
    "deliverables", "review_responsibilities", "collaboration_triggers", "target_capabilities",
    "evaluated_capabilities", "pending_capabilities", "evaluation_results", "selection_tags",
]
SEMANTIC_FIELDS = [
    "division", "specialty", "objects", "problems", "methods", "regime", "review_responsibilities",
]


def _mode_family(division: str) -> str:
    if division == "computation":
        return "computing"
    if division == "integration":
        return "integration"
    return "math" if division in {"topology", "algebraic_geometry", "categories"} else "physics"


def _tool_requirement(tool: str) -> dict:
    return {"name": tool, "availability": "probe_at_runtime", "required": False,
            "fallback": "entregar algoritmo y marcar cálculo pendiente si falta la herramienta",
            "use": "comprobación pertinente; disponibilidad no implica ejecución ni prueba general"}


def generate_profiles() -> list[dict]:
    """Return exactly 5,000 complete design profiles, deterministically."""
    profiles = []
    for division, expected in DIVISION_COUNTS.items():
        rows = _TRACK_ROWS[division]
        if len(rows) * 50 != expected:
            raise ValueError(f"taxonomy count mismatch in {division}")
        index = 0
        for track_index, row in enumerate(rows):
            specialty, object_, problem, main_method, regime = row.split("|")
            primary = PRIMARY_ARCHETYPES[division][track_index % len(PRIMARY_ARCHETYPES[division])]
            for mode_id, scope, mode_method, tool in MODE_SETS[_mode_family(division)]:
                for task_id, role, task, output, review, complementary in TASKS:
                    index += 1
                    complements = [complementary, "noether" if complementary != "noether" else "feynman"]
                    complements = list(dict.fromkeys(a for a in complements if a != primary))
                    if len(complements) < 2:
                        complements += [a for a in ["riemann", "weyl", "dirac"]
                                        if a != primary and a not in complements][:2-len(complements)]
                    target = {
                        "status": "design_target", "task": task, "line_problem": problem,
                        "scope": scope, "observable_output": output,
                        "acceptance": "resultado auditable con hipótesis, archivos y limitaciones; una obstrucción documentada es válida",
                    }
                    profiles.append({
                        "id": f"G5K-{division.upper()}-{index:04d}", "version": VERSION,
                        "division": division, "division_name": DIVISION_NAMES[division],
                        "specialty": specialty,
                        "subspecialties": [scope, task, *SPECIALIZED_KNOWLEDGE[division][:2]],
                        "competence_limits": [
                            f"Competencia objetivo delimitada a {specialty.lower()}; su rendimiento científico requiere evaluación individual.",
                            "No extrapolar un cálculo finito, local o perturbativo a un teorema global.",
                            "No atribuir equivalencia física, novedad ni solución del googly sin argumento y revisión específicos.",
                            f"El modo {mode_id} solo se aplica cuando sus hipótesis se justifican; registrar incompatibilidad y colaborar si no aplica.",
                        ],
                        "archetypes": {
                            "primary": primary, "complementary": complements,
                            "primary_method": ARCHETYPES[primary]["method"],
                            "combination_rationale": f"{ARCHETYPES[primary]['observable']}; complemento: {ARCHETYPES[complements[0]]['observable']}; aplicado a {task}.",
                            "status": "methodological_design_not_historical_equivalence",
                        },
                        "knowledge": {"common_core_target": COMMON_CORE,
                                      "specialized_target": SPECIALIZED_KNOWLEDGE[division],
                                      "training_status": "target_not_verified_qualification"},
                        "objects": [object_, f"Instancia delimitada: {scope}"],
                        "problems": [problem, f"En esa línea: {task}; alcance: {scope}."],
                        "methods": {
                            "primary": f"{main_method}; {mode_method}; finalidad: {task}",
                            "alternatives": ["reconstrucción desde definiciones y un ejemplo mínimo",
                                             f"contraste mediante {ARCHETYPES[complements[0]]['method']}"],
                            "compatibility_rationale": f"El objeto {object_} fija la línea; el modo modifica el alcance y la tarea exige {output}. Si el método no aplica, se documenta la obstrucción.",
                        },
                        "regime": f"{regime}; especialización operativa: {scope}",
                        "tools": [_tool_requirement("Python-stdlib"), *([] if tool == "Python-stdlib" else [_tool_requirement(tool)])],
                        "deliverables": [output, f"caso de {specialty.lower()} con hipótesis y fuentes identificadas",
                                         "informe de alcance, intentos de refutación y siguiente paso"],
                        "review_responsibilities": [review,
                            "reconstruir el paso decisivo en una ejecución distinta de la propuesta",
                            "separar revisión interna, evidencia computacional y revisión externa"],
                        "collaboration_triggers": [
                            "se necesita un teorema o herramienta fuera de la especialidad principal",
                            "hay incompatibilidad entre las hipótesis del modo y las del objeto",
                            "la interpretación física requiere firma, gauge o conteo de helicidades no fijados",
                            "un desacuerdo persiste tras reconstrucción y un cálculo independiente",
                            "se propone promover una afirmación a demostrada o formalmente verificada",
                        ],
                        "target_capabilities": [*QUALITY_TARGETS, target],
                        "evaluated_capabilities": [],
                        "pending_capabilities": [q["id"] for q in QUALITY_TARGETS] + [f"{division}:{track_index+1}:{mode_id}:{task_id}"],
                        "evaluation_results": [],
                        "selection_tags": list(dict.fromkeys([division, role, task_id, mode_id,
                                                             *PROGRAM_TAGS[division]])),
                        "design_axes": {"line": f"{division}:{track_index+1:02d}", "mode": mode_id,
                                        "task": task_id, "role": role},
                        "status": "registered_design_profile_not_executed_agent",
                    })
    return profiles


def _canonical(value) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", raw).casefold()).strip()


def semantic_fingerprint(profile: dict) -> str:
    """Ignore identifiers, versions and labels when looking for cloned work."""
    value = {key: profile.get(key) for key in SEMANTIC_FIELDS}
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def validate_profiles(profiles: list[dict], expected_counts: dict | None = None) -> dict:
    """Validate structural integrity and explicit diversity, not scientific skill.

    Near-neighbour reporting deliberately retains related profiles. Different
    tasks within one research line must share context. It is a warning about
    shared design, not an assertion of independent model capabilities.
    """
    expected_counts = DIVISION_COUNTS if expected_counts is None else expected_counts
    errors = []
    seen_ids, seen_semantic = set(), {}
    counts, roles, programs = Counter(), Counter(), Counter()
    line_coverage = defaultdict(lambda: {"modes": set(), "tasks": set(), "profiles": 0})
    dimensions = defaultdict(set)
    duplicate_pairs = []
    near_groups = defaultdict(list)
    malformed = 0
    for number, profile in enumerate(profiles, 1):
        if not isinstance(profile, dict):
            errors.append(f"row {number}: profile must be an object")
            malformed += 1
            continue
        identifier = profile.get("id", f"row:{number}")
        missing = [key for key in REQUIRED_FIELDS if key not in profile]
        if missing:
            errors.append(f"{identifier}: missing fields {missing}")
        if not isinstance(profile.get("id"), str) or not profile.get("id"):
            errors.append(f"row {number}: nonempty string id required")
        elif profile["id"] in seen_ids:
            errors.append(f"duplicate id: {profile['id']}")
        else:
            seen_ids.add(profile["id"])
        division = profile.get("division")
        if not isinstance(division, str):
            errors.append(f"{identifier}: division must be a string")
            division = "invalid"
        counts[division] += 1
        for key in ["version", "specialty", "regime"]:
            if not isinstance(profile.get(key), str) or not profile[key].strip():
                errors.append(f"{identifier}: nonempty string {key} required")
        for key in ["subspecialties", "competence_limits", "objects", "problems", "tools", "deliverables",
                    "review_responsibilities", "collaboration_triggers", "target_capabilities", "pending_capabilities", "selection_tags"]:
            if not isinstance(profile.get(key), list) or not profile[key]:
                errors.append(f"{identifier}: nonempty array {key} required")
        for key in ["evaluated_capabilities", "evaluation_results"]:
            if not isinstance(profile.get(key), list):
                errors.append(f"{identifier}: array {key} required (empty is honest before evaluation)")
        if not isinstance(profile.get("knowledge"), dict):
            errors.append(f"{identifier}: knowledge object required")
        else:
            core = profile["knowledge"].get("common_core_target")
            if not isinstance(core, list) or not all(isinstance(item, str) for item in core) or not set(COMMON_CORE).issubset(core):
                errors.append(f"{identifier}: common core incomplete")
        methods = profile.get("methods", {})
        if not isinstance(methods, dict) or not methods.get("primary") or not methods.get("alternatives"):
            errors.append(f"{identifier}: primary and alternative methods required")
        archetypes = profile.get("archetypes", {})
        if not isinstance(archetypes, dict) or archetypes.get("primary") not in ARCHETYPES:
            errors.append(f"{identifier}: valid primary archetype required")
        else:
            complements = archetypes.get("complementary")
            if not isinstance(complements, list) or not all(isinstance(item, str) for item in complements) or len(set(complements)) < 2 or any(a not in ARCHETYPES for a in complements):
                errors.append(f"{identifier}: two valid complementary archetypes required")
        # An evaluation must identify evidence. A declaration alone cannot pass.
        for evaluation in profile.get("evaluated_capabilities", []) if isinstance(profile.get("evaluated_capabilities"), list) else []:
            if not isinstance(evaluation, dict) or not evaluation.get("evidence") or not evaluation.get("run_id"):
                errors.append(f"{identifier}: evaluated capability lacks evidence and run_id")
        for tool in profile.get("tools", []) if isinstance(profile.get("tools"), list) else []:
            if not isinstance(tool, dict) or tool.get("availability") != "probe_at_runtime":
                errors.append(f"{identifier}: tool availability must be checked at runtime")
        if missing:
            malformed += 1
            continue
        fingerprint = semantic_fingerprint(profile)
        if fingerprint in seen_semantic:
            duplicate_pairs.append([seen_semantic[fingerprint], identifier])
        else:
            seen_semantic[fingerprint] = identifier
        axes = profile.get("design_axes", {})
        if not isinstance(axes, dict) or not all(axes.get(x) for x in ["line", "mode", "task", "role"]):
            errors.append(f"{identifier}: explicit design axes required")
        else:
            line = axes["line"]
            line_coverage[line]["profiles"] += 1
            line_coverage[line]["modes"].add(axes["mode"])
            line_coverage[line]["tasks"].add(axes["task"])
            roles[axes["role"]] += 1
            # Same line and mode: deliberately shared context, distinct task.
            near_groups[(line, axes["mode"])].append(identifier)
        for key in ["specialty", "objects", "problems", "methods", "regime", "review_responsibilities"]:
            dimensions[key].add(_canonical(profile.get(key)))
        for tag in profile.get("selection_tags", []) if isinstance(profile.get("selection_tags"), list) else []:
            if tag in {"googly", "quantum_gravity", "unified_field_theory"}:
                programs[tag] += 1
    if counts != Counter(expected_counts):
        errors.append(f"division distribution mismatch: expected {dict(expected_counts)}, got {dict(counts)}")
    if len(profiles) != sum(expected_counts.values()):
        errors.append(f"expected {sum(expected_counts.values())} profiles, got {len(profiles)}")
    if duplicate_pairs:
        errors.append(f"semantic duplicates detected: {len(duplicate_pairs)}")
    if expected_counts == DIVISION_COUNTS:
        expected_lines = {f"{division}:{index+1:02d}" for division, rows in _TRACK_ROWS.items() for index in range(len(rows))}
        if set(line_coverage) != expected_lines:
            errors.append("research-line coverage differs from the maintained taxonomy")
        for line, value in line_coverage.items():
            if value["profiles"] != 50 or len(value["modes"]) != 5 or len(value["tasks"]) != 10:
                errors.append(f"{line}: expected 50 profiles covering five modes and ten tasks")
    shared = [{"line": line, "mode": mode, "profiles": len(ids),
               "reason": "shared research line and scope; task and required output differ",
               "ids": ids}
              for (line, mode), ids in near_groups.items() if len(ids) > 1]
    return {
        "valid": not errors, "errors": errors, "profile_count": len(profiles),
        "division_counts": dict(counts), "schema_version": VERSION,
        "uniqueness": {"unique_ids": len(seen_ids), "semantic_fingerprints": len(seen_semantic),
                       "exact_semantic_duplicate_pairs": duplicate_pairs, "malformed_rows": malformed},
        "coverage": {
            "scientific_lines": len(line_coverage), "roles": dict(roles), "program_tags": dict(programs),
            "distinct_dimension_counts": {k: len(v) for k, v in dimensions.items()},
            "lines": {key: {"profiles": value["profiles"], "modes": sorted(value["modes"]),
                             "tasks": sorted(value["tasks"])} for key, value in line_coverage.items()},
        },
        "proximity": {"shared_context_groups": len(shared), "examples": shared[:10],
                      "interpretation": "Structural sharing is reported, not concealed. Semantic and scientific originality require human/task-specific review."},
        "capability_status": {"scientific_evaluation": "pending_individual_runs",
                              "integrity_validation": "passed" if not errors else "failed",
                              "registered_profiles_are_not_executed_agents": True},
    }


def load_profiles(path: Path | str) -> list[dict]:
    path = Path(path)
    if path.is_dir():
        path = path / "institute" / "registry" / "profiles.jsonl"
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def profile_schema() -> dict:
    """Portable JSON Schema; runtime validation does not need jsonschema."""
    nonempty_array = {"type": "array", "minItems": 1}
    properties = {key: {"type": "string", "minLength": 1}
                  for key in ["id", "version", "division", "specialty", "regime"]}
    properties["division"]["enum"] = list(DIVISION_COUNTS)
    for key in ["subspecialties", "competence_limits", "objects", "problems", "tools", "deliverables",
                "review_responsibilities", "collaboration_triggers", "target_capabilities", "pending_capabilities", "selection_tags"]:
        properties[key] = dict(nonempty_array)
    for key in ["evaluation_results", "evaluated_capabilities"]:
        properties[key] = {"type": "array"}
    properties["methods"] = {"type": "object", "required": ["primary", "alternatives", "compatibility_rationale"]}
    properties["archetypes"] = {"type": "object", "required": ["primary", "complementary", "combination_rationale", "status"]}
    properties["knowledge"] = {"type": "object", "required": ["common_core_target", "specialized_target", "training_status"]}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "GENIUS-5000 profile",
            "type": "object", "required": REQUIRED_FIELDS + ["design_axes", "status"],
            "properties": properties, "additionalProperties": True}


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_catalogue(root: Path | str) -> dict:
    """Write full records, taxonomy, design reference library and integrity report."""
    root = Path(root)
    profiles = generate_profiles()
    report = validate_profiles(profiles)
    if not report["valid"]:
        raise ValueError("catalogue integrity failed: " + "; ".join(report["errors"]))
    registry = root / "institute" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    output = registry / "profiles.jsonl"
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for profile in profiles:
            stream.write(json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    _write_json(registry / "schema.json", profile_schema())
    _write_json(root / "institute" / "archetypes" / "library.json", {
        "version": VERSION, "status": "methodological_design", "archetypes": ARCHETYPES,
        "attribution": "Methods assigned by the institute; no impersonation, credentials, IQ scores or measured historical equivalence.",
        "reference_status": "Provided biographical links identify referents; scientific claims require their own consulted primary references.",
    })
    _write_json(root / "institute" / "divisions" / "taxonomy.json", {
        "version": VERSION, "counts": DIVISION_COUNTS, "names": DIVISION_NAMES,
        "track_fields": ["specialty", "object", "problem", "method", "regime"],
        "tracks": {division: [row.split("|") for row in rows] for division, rows in _TRACK_ROWS.items()},
        "modes": MODE_SETS, "tasks": TASKS,
    })
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    report["artifact"] = {"path": "institute/registry/profiles.jsonl", "sha256": digest,
                          "bytes": output.stat().st_size, "deterministic": True}
    _write_json(root / "institute" / "evaluations" / "catalogue_validation.json", report)
    _write_json(registry / "manifest.json", {"version": VERSION, "profile_count": len(profiles),
                                            "distribution": DIVISION_COUNTS, "profiles_sha256": digest,
                                            "scientific_capabilities_evaluated": 0,
                                            "scientific_evaluation_status": "pending",
                                            "generation": "python -m genius catalogue"})
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = write_catalogue(args.root)
    print(json.dumps({"valid": result["valid"], "profile_count": result["profile_count"],
                      "division_counts": result["division_counts"], "artifact": result["artifact"]}, ensure_ascii=False, indent=2))
