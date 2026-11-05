# Caso de referencia: dualidad de Hodge en dimensión cuatro

Este caso conocido comprueba el flujo de selección, cálculo y auditoría. No mide
capacidad de resolver investigación abierta ni constituye una solución del Googly.
El backend `genius.benchmark` ejecuta aritmética exacta estándar y declara que no
es una ejecución de Claude o Codex. Su revisión es interna y comparte código.

## Enunciado y premisas (B1–B2)

Sea $V=\mathbb R^4$ con métrica euclídea, coframe ortonormal
$(e^1,e^2,e^3,e^4)$ y orientación $\operatorname{vol}=e^{1234}$.
En $\Lambda^2V^*$, definir $*$ por
$\alpha\wedge *\beta=\langle\alpha,\beta\rangle\operatorname{vol}$.
Se comprueba el resultado conocido $*^2=I$ y que los autoespacios reales de
autovalores $+1,-1$ tienen dimensión tres. Es una especialización, sin novedad
bibliográfica pretendida. La regla de cuadrado y su contexto figuran en la
[documentación oficial de SageMath](https://doc.sagemath.org/html/en/reference/algebras/sage/algebras/clifford_algebra_element.html#sage.algebras.clifford_algebra_element.ExteriorAlgebraElement.hodge_dual).

## Argumento explícito (B3–B4)

1. La base exterior ordenada es $(e^{12},e^{13},e^{14},e^{23},e^{24},e^{34})$.
2. El emparejamiento exterior en la definición da
   $*e^{12}=e^{34}$, $*e^{13}=-e^{24}$ y $*e^{14}=e^{23}$.
   Por ejemplo $e^{13}\wedge e^{24}=-\operatorname{vol}$, que fija el signo.
3. Las imágenes complementarias son $*e^{34}=e^{12}$,
   $*e^{24}=-e^{13}$ y $*e^{23}=e^{14}$ por el mismo emparejamiento.
4. Aplicar $*$ dos veces a cada base devuelve esa base. Por linealidad $*^2=I$.
5. Los vectores $(e^{12}+e^{34},e^{13}-e^{24},e^{14}+e^{23})$ tienen
   autovalor $+1$; cambiar los signos entre pares da tres vectores de autovalor
   $-1$. Son seis vectores linealmente independientes, pues cada par tiene
   determinante no nulo. Agotan la dimensión seis y cada autoespacio tiene dimensión tres.

Es un argumento del caso finito declarado. Los resultados guardados por el backend
se clasifican como evidencia simbólica o numérica exacta; no se promueven a un teorema
general mediante la ejecución de un script.

## Refutación y límites (B5–B6, A4–A7)

La propuesta deliberadamente incorrecta $*^2=-I$ falla en $e^{12}$:
$*^2e^{12}=e^{12}\ne-e^{12}$. La diferencia es $2e^{12}$ sobre los reales.
En firma con un único signo negativo el cuadrado en dos formas sí cambia a $-I$;
por ello la firma debe formar parte del enunciado. Aquí las cantidades son
adimensionales y no hay ecuaciones de campo, gauge, condiciones de contorno o
límite dinámico: no se recuperan grados de libertad gravitatorios por este cálculo.

El productor calcula con complementos y paridad. El auditor reconstruye la matriz
invirtiendo el emparejamiento exterior y usando determinantes de permutación. Esa
ruta puede detectar signos o rangos falsificados; sigue siendo una revisión interna
del mismo repositorio y no un contraste entre modelos independiente.

El auditor verifica todos los productores suministrados, sus convenciones y la
evidencia adjunta a cada afirmación. Guarda veredictos por ejecución; una segunda
instantánea incompatible con el mismo ID se rechaza. Sólo refuta la propuesta
deliberada cuando su enunciado e hipótesis coinciden con el caso declarado: reutilizar
su ID para un texto corregido no autoriza una refutación automática.

Para ejecutar el caso desde una consola Python:

```python
from genius.benchmark import run_reference
report = run_reference("runs/reference-hodge")
assert report["passed"]
```

Los tests alteran además signo, cuadrado y rango del artefacto productor para
verificar que el auditor no confirma esas versiones.
