"""
Chart generation utilities using matplotlib.
"""

import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


def generate_grade_distribution_chart(grades, title='Distribución de Notas'):
    """
    Generate a histogram of grade distribution.
    
    Args:
        grades: List of grade scores
        title: Chart title
    
    Returns:
        str: Base64 encoded image
    """
    if not grades:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create histogram
    bins = np.arange(1.0, 5.5, 0.5)
    ax.hist(grades, bins=bins, edgecolor='black', alpha=0.7, color='#4CAF50')
    
    # Add vertical line at passing grade
    ax.axvline(x=3.0, color='red', linestyle='--', linewidth=2, label='Mínimo aprobatorio (3.0)')
    
    ax.set_xlabel('Calificación')
    ax.set_ylabel('Número de Estudiantes')
    ax.set_title(title)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Save to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=100)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    plt.close()
    
    return img_base64


def generate_pie_chart_pass_fail(passed, failed, title='Estado de Aprobación'):
    """
    Generate a pie chart of passed vs failed.
    
    Args:
        passed: Number of students who passed
        failed: Number of students who failed
        title: Chart title
    
    Returns:
        str: Base64 encoded image
    """
    if passed == 0 and failed == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sizes = [passed, failed]
    labels = ['Aprobado', 'Reprobado']
    colors = ['#4CAF50', '#F44336']
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12}
    )
    
    ax.set_title(title)
    
    # Save to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=100)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    plt.close()
    
    return img_base64


def generate_bar_chart_comparison(data, labels, title='Comparación de Rendimiento'):
    """
    Generate a bar chart for comparing multiple groups/subjects.
    
    Args:
        data: List of lists with numeric values
        labels: List of labels for each bar
        title: Chart title
    
    Returns:
        str: Base64 encoded image
    """
    if not data or not labels:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(labels))
    width = 0.35
    
    # Create bars for each dataset
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0']
    for i, dataset in enumerate(data):
        color = colors[i % len(colors)]
        ax.bar(x + i * width, dataset, width, label=f'Grupo {i+1}', color=color, edgecolor='black', alpha=0.7)
    
    ax.set_xlabel('Grupos/Materias')
    ax.set_ylabel('Promedio de Calificación')
    ax.set_title(title)
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(1.0, 5.0)
    
    plt.tight_layout()
    
    # Save to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=100)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    plt.close()
    
    return img_base64


def generate_line_chart_trends(data, period_labels, title='Tendencia de Rendimiento'):
    """
    Generate a line chart showing trends over periods.
    
    Args:
        data: List of numeric values for each period
        period_labels: List of period names
        title: Chart title
    
    Returns:
        str: Base64 encoded image
    """
    if not data or not period_labels:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(period_labels, data, marker='o', linewidth=2, markersize=8, color='#2196F3')
    ax.fill_between(range(len(data)), data, alpha=0.1, color='#2196F3')
    
    # Add passing line
    ax.axhline(y=3.0, color='red', linestyle='--', linewidth=2, label='Mínimo aprobatorio')
    
    ax.set_xlabel('Periodo Académico')
    ax.set_ylabel('Promedio de Calificación')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(1.0, 5.0)
    
    # Add value labels
    for i, value in enumerate(data):
        ax.annotate(f'{value:.1f}', (i, value), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    # Save to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=100)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    plt.close()
    
    return img_base64


def generate_heatmap_data(data, row_labels, col_labels, title='Mapa de Calor - Rendimiento'):
    """
    Generate a heatmap image from data matrix.
    
    Args:
        data: 2D array of values
        row_labels: Labels for rows
        col_labels: Labels for columns
        title: Chart title
    
    Returns:
        str: Base64 encoded image
    """
    if not data or not row_labels or not col_labels:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create heatmap
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto')
    
    # Set ticks
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add text annotations
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            text = ax.text(j, i, f'{data[i, j]:.1f}',
                         ha="center", va="center", color="black", fontsize=9)
    
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label='Promedio de Calificación')
    
    plt.tight_layout()
    
    # Save to base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=100)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    plt.close()
    
    return img_base64
