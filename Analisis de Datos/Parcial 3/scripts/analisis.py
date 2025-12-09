import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer

# CARGA DE DATOS
df = pd.read_csv('../data/RespuestasSanitizadas.csv')

print("=" * 80)
print("INFORMACIÓN GENERAL DEL DATASET")
print("=" * 80)
print(f"Dimensiones: {df.shape}")
print(f"Número de estudiantes: {df.shape[0]}")
print(f"Número de variables: {df.shape[1]}")
print("\nPrimeras columnas:")
print(df.columns.tolist()[:10])

# SELECCIÓN DE VARIABLES NUMÉRICAS Y CATEGÓRICAS

# CSV ya sanitizado
# Variables numéricas continuas
numeric_continuous = [
    'Edad',
    'HorasTrabajo',
    'HorasEstudio',
    'RendimientoProgramacion',
    'TiempoHogarEscuela',
    'HorasDeSueno',
    'TiempoEjercicioSemana',
    'ConsumoCafeina',
    'ConsumoCafe',
    'ConsumoBebidaAzucarada',
    'UsoVideojuegos',
    'PensamientoLogico1',
    'PensamientoLogico2',
    'PensamientoLogico3',
    'PensamientoLogico4',
    'ResilienciaFrustracion1',
    'ResilienciaFrustracion2',
    'ResilienciaFrustracion3',
    'ResilienciaFrustracion4',
    'ResilienciaFrustracion5'
]

# Variables binarias
binary_columns = [
    'Genero_Femenino',
    'Genero_Masculino',
    'Genero_Prefiero no decirlo',
    'DescalcificacionEnGestacion_No',
    'DescalcificacionEnGestacion_No lo sé',
    'DescalcificacionEnGestacion_Sí',
    'ConsumioOmega3_No',
    'ConsumioOmega3_No lo sé',
    'ConsumioOmega3_Sí',
    'FamiliaDisfuncional_No',
    'FamiliaDisfuncional_Sí',
    'FamiliaDisfuncional_Tal vez',
    'AhorroEnInfancia',
    'TrabajoEnInfancia',
    'TipoEscuelaPrevia_Escuela privada (colegios)',
    'TipoEscuelaPrevia_Escuela pública',
    'ExperienciaPrevia',
    'DietaBalanceada_A veces',
    'DietaBalanceada_No',
    'DietaBalanceada_Sí',
    'ConsumeEstupefaciente',
    'ConsumeEstupefacienteControl',
    'MedicadoPrevioCarrera'
]

# Variables de actividades
activity_columns = [
    'ActividadesEnInfancia_JuegoFisico',
    'ActividadesEnInfancia_JuegoCreativo',
    'ActividadesEnInfancia_JuegoSimbolico',
    'ActividadesEnInfancia_JuegoTecnologico',
    'ActividadesEnInfancia_ActividadesSocioCulturales',
    'ExperienciaPreviaLogica_Ajedrez',
    'ExperienciaPreviaLogica_Debate',
    'ExperienciaPreviaLogica_Filosofia',
    'ExperienciaPreviaLogica_Matematicas',
    'MetodoDeEstudio_MapasConceptuales',
    'MetodoDeEstudio_Resumenes',
    'MetodoDeEstudio_Lectura',
    'MetodoDeEstudio_Ejercicios',
    'MetodoDeEstudio_VideosTutoriales',
    'ActividadesExtra_Laborales',
    'ActividadesExtra_TareasHogar',
    'ActividadesExtra_CuidadoFamiliar',
    'ActividadesExtra_CompromisoSocial'
]

# Variables de nivel/ordinal
ordinal_columns = [
    'NivelIngles_Avanzado',
    'NivelIngles_Básico',
    'NivelIngles_Intermedio',
    'NivelIngles_Nativo',
    'NivelInstrumentoMusical_Avanzado',
    'NivelInstrumentoMusical_Intermedio',
    'NivelInstrumentoMusical_No sé tocar un instrumento',
    'NivelInstrumentoMusical_Novato'
]

# Variables de frecuencia de uso de IA
ia_columns = [
    'UsoHerramientasIA_A veces (pocas veces al mes)',
    'UsoHerramientasIA_Diariamente',
    'UsoHerramientasIA_Frecuentemente (varias veces por semana)',
    'UsoHerramientasIA_Nunca'
]

# Tipo de aprendizaje
learning_columns = [
    'TipoAprendizaje_Auditivo (prefiero escuchar explicaciones)',
    'TipoAprendizaje_Kinestésico (prefiero hacer las cosas, practicar)',
    'TipoAprendizaje_Visual (prefiero diagramas, videos)'
]

# Combinar todas las columnas seleccionadas
selected_columns = (
    numeric_continuous + 
    binary_columns + 
    activity_columns + 
    ordinal_columns + 
    ia_columns + 
    learning_columns
)

# CREAR DATAFRAME CON VARIABLES SELECCIONADAS
existing_columns = [col for col in selected_columns if col in df.columns]

# Crear DataFrame con las columnas existentes
df_numeric = df[existing_columns].copy()

# Convertir todas las columnas a numérico, forzando errores a NaN
for col in df_numeric.columns:
    df_numeric[col] = pd.to_numeric(df_numeric[col], errors='coerce')


# Mostrar resumen de valores faltantes antes de imputar
missing_summary = df_numeric.isnull().sum()
missing_summary = missing_summary[missing_summary > 0].sort_values(ascending=False)

if len(missing_summary) > 0:
    print("\nVariables con valores faltantes:")
    for col, count in missing_summary.head(10).items():
        print(f"  {col}: {count} ({count/len(df_numeric)*100:.1f}%)")
    if len(missing_summary) > 10:
        print(f"  ... y {len(missing_summary) - 10} variables más")
    print(f"\nPorcentaje total de valores faltantes: {df_numeric.isnull().sum().sum() / (df_numeric.shape[0] * df_numeric.shape[1]) * 100:.2f}%")
else:
    print("\n✓ No hay valores faltantes en el dataset")

# Imputar con la mediana
imputer = SimpleImputer(strategy='median')
df_imputed = pd.DataFrame(
    imputer.fit_transform(df_numeric),
    columns=df_numeric.columns,
    index=df_numeric.index
)

print(f"\nImputación completada usando la mediana")
print(f"Valores faltantes después de imputación: {df_imputed.isnull().sum().sum()}")

# ESCALADO DE DATOS
print("\n" + "=" * 80)
print("ESCALADO DE DATOS")
print("=" * 80)

scaler = StandardScaler()
df_scaled = pd.DataFrame(
    scaler.fit_transform(df_imputed),
    columns=df_imputed.columns,
    index=df_imputed.index
)

print("Datos escalados usando StandardScaler (media=0, std=1)")
print(f"Shape de datos escalados: {df_scaled.shape}")
print(f"\nEstadísticas después del escalado:")
print(f"Media de todas las columnas: {df_scaled.mean().mean():.6f}")
print(f"Desviación estándar promedio: {df_scaled.std().mean():.6f}")

# APLICACIÓN DE ISOLATION FOREST

print("\n" + "=" * 80)
print("APLICACIÓN DE ISOLATION FOREST")
print("=" * 80)

# Configurar el modelo con enfoque conservador
contamination_rate = 0.03  # 3% de anomalías esperadas
random_state = 42

iso_forest = IsolationForest(
    contamination=contamination_rate,
    random_state=random_state,
    n_estimators=100,
    max_samples='auto',
    max_features=1.0,
    bootstrap=False,
    n_jobs=-1,
    verbose=0
)

print(f"Configuración del modelo:")
print(f"  - Contamination rate: {contamination_rate} ({contamination_rate*100}%)")
print(f"  - Número de árboles: 100")
print(f"  - Random state: {random_state}")

# Entrenar el modelo
print("\nEntrenando Isolation Forest")
iso_forest.fit(df_scaled)

# Obtener predicciones y scores
predictions = iso_forest.predict(df_scaled)
anomaly_scores = iso_forest.decision_function(df_scaled)

# Convertir predicciones: -1 (anómalo) y 1 (normal)
df_results = df_imputed.copy()
df_results['anomaly'] = predictions
df_results['anomaly_score'] = anomaly_scores
df_results['is_anomaly'] = (predictions == -1).astype(int)

print("Modelo entrenado exitosamente")

# EVALUACIÓN DE RESULTADOS
print("\n" + "=" * 80)
print("EVALUACIÓN DE RESULTADOS")
print("=" * 80)

n_anomalies = (predictions == -1).sum()
n_normal = (predictions == 1).sum()
pct_anomalies = (n_anomalies / len(predictions)) * 100

print(f"\nResultados de detección:")
print(f"  - Total de estudiantes: {len(predictions)}")
print(f"  - Estudiantes normales: {n_normal} ({(n_normal/len(predictions)*100):.1f}%)")
print(f"  - Estudiantes anómalos: {n_anomalies} ({pct_anomalies:.1f}%)")

print(f"\nEstadísticas de anomaly scores:")
print(f"  - Score mínimo: {anomaly_scores.min():.4f}")
print(f"  - Score máximo: {anomaly_scores.max():.4f}")
print(f"  - Score promedio: {anomaly_scores.mean():.4f}")
print(f"  - Mediana de scores: {np.median(anomaly_scores):.4f}")

# Identificar los estudiantes más anómalos
anomaly_indices = np.where(predictions == -1)[0]
print(f"\nÍndices de estudiantes anómalos: {anomaly_indices.tolist()}")

# ANÁLISIS DE PATRONES EN ANOMALÍAS

print("\n" + "=" * 80)
print("ANÁLISIS DE PATRONES EN ANOMALÍAS")
print("=" * 80)

# Comparar promedios entre normales y anómalos
if n_anomalies > 0:
    comparison = pd.DataFrame({
        'Normal': df_results[df_results['anomaly'] == 1].drop(['anomaly', 'anomaly_score', 'is_anomaly'], axis=1).mean(),
        'Anómalo': df_results[df_results['anomaly'] == -1].drop(['anomaly', 'anomaly_score', 'is_anomaly'], axis=1).mean()
    })
    comparison['Diferencia'] = comparison['Anómalo'] - comparison['Normal']
    comparison['Dif_Absoluta'] = comparison['Diferencia'].abs()
    comparison = comparison.sort_values('Dif_Absoluta', ascending=False)
    
    print("\nTop 15 variables con mayor diferencia entre normales y anómalos:")
    print(comparison.head(15))
else:
    print("\nNo se detectaron anomalías con el contamination rate actual")
    comparison = pd.DataFrame()

# VERIFICACIÓN DE ETIQUETAS

print("\n" + "=" * 80)
print("VERIFICACIÓN DE ETIQUETAS")
print("=" * 80)

print("\nDistribución de etiquetas 'anomaly':")
print(df_results['anomaly'].value_counts())

if n_anomalies > 0:
    print("\n--- Ejemplos de estudiantes NORMALES ---")
    normal_examples = df_results[df_results['anomaly'] == 1][['Edad', 'RendimientoProgramacion', 'HorasEstudio', 'anomaly', 'anomaly_score']].head(3)
    for idx, row in normal_examples.iterrows():
        print(f"\nEstudiante {idx}:")
        print(f"  Edad: {row['Edad']:.0f}")
        print(f"  Rendimiento: {row['RendimientoProgramacion']:.0f}")
        print(f"  Horas estudio: {row['HorasEstudio']:.0f}")
        print(f"  Etiqueta: {row['anomaly']}")
        print(f"  Score: {row['anomaly_score']:.4f}")
    
    print("\n--- Ejemplos de estudiantes ANÓMALOS ---")
    anomaly_examples = df_results[df_results['anomaly'] == -1][['Edad', 'RendimientoProgramacion', 'HorasEstudio', 'anomaly', 'anomaly_score']].head(3)
    for idx, row in anomaly_examples.iterrows():
        print(f"\nEstudiante {idx}:")
        print(f"  Edad: {row['Edad']:.0f}")
        print(f"  Rendimiento: {row['RendimientoProgramacion']:.0f}")
        print(f"  Horas estudio: {row['HorasEstudio']:.0f}")
        print(f"  Etiqueta: {row['anomaly']}")
        print(f"  Score: {row['anomaly_score']:.4f}")

# VISUALIZACIONES

print("\n" + "=" * 80)
print("GENERANDO VISUALIZACIONES")
print("=" * 80)

# 10.1 PCA 2D con anomalías resaltadas
print("\n1. Generando PCA 2D")
pca = PCA(n_components=2, random_state=random_state)
pca_coords = pca.fit_transform(df_scaled)

plt.figure(figsize=(12, 8))
scatter = plt.scatter(
    pca_coords[:, 0],
    pca_coords[:, 1],
    c=['red' if x == -1 else 'green' for x in predictions],
    alpha=0.6,
    s=100,
    edgecolors='black',
    linewidth=0.5
)

# Anotar los puntos anómalos con su índice
for idx in anomaly_indices:
    plt.annotate(
        f'{idx}',
        (pca_coords[idx, 0], pca_coords[idx, 1]),
        fontsize=9,
        fontweight='bold',
        color='darkred'
    )

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varianza)', fontsize=12)
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varianza)', fontsize=12)
plt.title('Detección de Anomalías usando Isolation Forest\n(PCA 2D)', fontsize=14, fontweight='bold')
plt.legend(['Anómalo', 'Normal'], loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./results-anomaly-non-supervised/isolation_forest_pca2d.png', dpi=300, bbox_inches='tight')
print("Gráfico PCA 2D guardado como 'isolation_forest_pca2d.png'")
plt.show()

# 10.2 Histograma de anomaly scores
print("\n2. Generando histograma de anomaly scores...")
plt.figure(figsize=(12, 6))
plt.hist(anomaly_scores, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
threshold = np.percentile(anomaly_scores, contamination_rate*100)
plt.axvline(threshold, 
            color='red', linestyle='--', linewidth=2, 
            label=f'Umbral de anomalía (percentil {contamination_rate*100})')
plt.xlabel('Anomaly Score', fontsize=12)
plt.ylabel('Frecuencia', fontsize=12)
plt.title('Distribución de Anomaly Scores\nIsolation Forest', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./results-anomaly-non-supervised/anomaly_scores_histogram.png', dpi=300, bbox_inches='tight')
print("Histograma guardado como 'anomaly_scores_histogram.png'")
plt.show()

# 10.3 Boxplots de las top variables con mayor diferencia
if n_anomalies > 0 and len(comparison) > 0:
    print("\n3. Generando boxplots de variables destacadas...")
    top_vars = comparison.head(8).index.tolist()
    
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()
    
    for idx, var in enumerate(top_vars):
        ax = axes[idx]
        data_to_plot = [
            df_results[df_results['anomaly'] == 1][var],
            df_results[df_results['anomaly'] == -1][var]
        ]
        bp = ax.boxplot(data_to_plot, tick_labels=['Normal', 'Anómalo'], patch_artist=True)
        
        # Colorear las cajas
        bp['boxes'][0].set_facecolor('lightgreen')
        bp['boxes'][1].set_facecolor('lightcoral')
        
        ax.set_title(var, fontsize=10, fontweight='bold')
        ax.set_ylabel('Valor', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Comparación de Variables entre Estudiantes Normales y Anómalos\n(Top 8 variables con mayor diferencia)', 
                 fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()
    plt.savefig('./results-anomaly-non-supervised/boxplots_top_variables.png', dpi=300, bbox_inches='tight')
    print("Boxplots guardados como 'boxplots_top_variables.png'")
    plt.show()
else:
    print("\nSaltando boxplots (no hay suficientes anomalías)")

# 10.4 Violin plots para algunas variables clave
print("\n4. Generando violin plots...")
key_vars = ['RendimientoProgramacion', 'HorasEstudio', 'UsoVideojuegos', 'Edad']
key_vars = [v for v in key_vars if v in df_results.columns]

if len(key_vars) > 0 and n_anomalies > 0:
    fig, axes = plt.subplots(1, len(key_vars), figsize=(16, 5))
    if len(key_vars) == 1:
        axes = [axes]
    
    for idx, var in enumerate(key_vars):
        ax = axes[idx]
        
        # Preparar datos
        normal_data = df_results[df_results['anomaly'] == 1][var]
        anomaly_data = df_results[df_results['anomaly'] == -1][var]
        
        parts = ax.violinplot([normal_data, anomaly_data], 
                              positions=[1, 2], 
                              showmeans=True, 
                              showmedians=True)
        
        # Colorear
        for pc, color in zip(parts['bodies'], ['lightgreen', 'lightcoral']):
            pc.set_facecolor(color)
            pc.set_alpha(0.7)
        
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['Normal', 'Anómalo'])
        ax.set_title(var, fontsize=11, fontweight='bold')
        ax.set_ylabel('Valor', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Distribución de Variables Clave por Tipo de Estudiante', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('./results-anomaly-non-supervised/violin_plots_key_variables.png', dpi=300, bbox_inches='tight')
    print("Violin plots guardados como 'violin_plots_key_variables.png'")
    plt.show()
else:
    print("\nSaltando violin plots (no hay suficientes anomalías o variables)")

# 10.5 Heatmap de correlación de anomalías (BONUS)
if n_anomalies > 0 and len(comparison) > 0:
    print("\n5. Generando heatmap de variables más diferenciadas...")
    top_10_vars = comparison.head(10).index.tolist()
    
    # Crear un subset con las top 10 variables
    heatmap_data = df_results[df_results['anomaly'] == -1][top_10_vars].T
    
    plt.figure(figsize=(14, 8))
    sns.heatmap(heatmap_data, cmap='RdYlGn_r', center=0, 
                cbar_kws={'label': 'Valor Escalado'},
                linewidths=0.5, linecolor='gray')
    plt.title('Perfil de Estudiantes Anómalos\n(Top 10 Variables Distintivas)', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Índice de Estudiante Anómalo', fontsize=11)
    plt.ylabel('Variable', fontsize=11)
    plt.tight_layout()
    plt.savefig('./results-anomaly-non-supervised/heatmap_anomalias.png', dpi=300, bbox_inches='tight')
    print("Heatmap guardado como 'heatmap_anomalias.png'")
    plt.show()

# ANÁLISIS DETALLADO DE CASOS ANÓMALOS

print("\n" + "=" * 80)
print("ANÁLISIS DETALLADO DE ESTUDIANTES ANÓMALOS")
print("=" * 80)

if n_anomalies > 0:
    # Obtener datos originales de los estudiantes anómalos
    anomalous_students = df.iloc[anomaly_indices].copy()
    anomalous_students['anomaly_score'] = anomaly_scores[anomaly_indices]
    anomalous_students = anomalous_students.sort_values('anomaly_score')
    
    print(f"\nSe detectaron {n_anomalies} estudiantes anómalos:")
    print("\nCaracterísticas principales de los estudiantes anómalos:")
    
    # Mostrar información relevante de cada estudiante anómalo
    relevant_cols = ['Edad', 'HorasTrabajo', 'ExperienciaPrevia', 
                     'HorasEstudio', 'RendimientoProgramacion',
                     'HorasDeSueno', 'UsoVideojuegos', 'anomaly_score']
    relevant_cols = [col for col in relevant_cols if col in anomalous_students.columns]
    
    for idx, (original_idx, row) in enumerate(anomalous_students.iterrows(), 1):
        print(f"\n{'='*60}")
        print(f"ESTUDIANTE ANÓMALO #{idx} (Índice {original_idx})")
        print(f"{'='*60}")
        print(f"Anomaly Score: {row['anomaly_score']:.4f}")
        print(f"\nPerfil:")
        for col in relevant_cols[:-1]:  # Excluir anomaly_score
            if col in row:
                print(f"  • {col}: {row[col]}")
    
    # Exportar resultados detallados
    output_file = './results-anomaly-non-supervised/estudiantes_anomalos_detalle.csv'
    anomalous_students.to_csv(output_file, index=True)
    print(f"\nDetalles completos exportados a '{output_file}'")
else:
    print("\nNo se detectaron estudiantes anómalos con el contamination rate actual")

# RESUMEN FINAL Y EXPORTACIÓN

print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)

summary = {
    'Total estudiantes': len(df_results),
    'Estudiantes normales': n_normal,
    'Estudiantes anómalos': n_anomalies,
    'Porcentaje anomalías': f"{pct_anomalies:.2f}%",
    'Contamination rate': contamination_rate,
    'Número de features': df_scaled.shape[1],
    'Varianza explicada PC1': f"{pca.explained_variance_ratio_[0]*100:.2f}%",
    'Varianza explicada PC2': f"{pca.explained_variance_ratio_[1]*100:.2f}%",
    'Varianza total (PC1+PC2)': f"{sum(pca.explained_variance_ratio_[:2])*100:.2f}%",
    'Score mínimo': f"{anomaly_scores.min():.4f}",
    'Score máximo': f"{anomaly_scores.max():.4f}"
}

for key, value in summary.items():
    print(f"{key}: {value}")

# Guardar todos los resultados
df_results.to_csv('./results-anomaly-non-supervised/resultados_isolation_forest.csv', index=False)
print(f"\nResultados completos guardados en 'resultados_isolation_forest.csv'")

# Guardar comparación de variables
if len(comparison) > 0:
    comparison.to_csv('./results-anomaly-non-supervised/comparacion_variables_normal_vs_anomalo.csv')
    print(f"Comparación de variables guardada en 'comparacion_variables_normal_vs_anomalo.csv'")

print("\n" + "=" * 80)
print("ANÁLISIS COMPLETADO EXITOSAMENTE")
print("=" * 80)

archivos_generados = [
    "1. isolation_forest_pca2d.png",
    "2. anomaly_scores_histogram.png"
]

if n_anomalies > 0:
    archivos_generados.extend([
        "3. boxplots_top_variables.png",
        "4. violin_plots_key_variables.png",
        "5. heatmap_anomalias.png",
        "6. resultados_isolation_forest.csv",
        "7. comparacion_variables_normal_vs_anomalo.csv",
        "8. estudiantes_anomalos_detalle.csv"
    ])
else:
    archivos_generados.append("3. resultados_isolation_forest.csv")

print("\nArchivos generados:")
for archivo in archivos_generados:
    print(f"  {archivo}")