"""Script to visualize the LangGraph workflow."""
from IPython.display import Image, display
from app.graph.builder import build_graph


def visualize_graph():
    """Build and visualize the LangGraph workflow."""
    graph = build_graph()
    
    # Generate mermaid PNG
    png_data = graph.get_graph().draw_mermaid_png()
    
    # Display in Jupyter notebook
    display(Image(png_data))
    
    return graph


if __name__ == "__main__":
    # For non-Jupyter environments, save to file
    from pathlib import Path
    
    graph = build_graph()
    png_data = graph.get_graph().draw_mermaid_png()
    
    output_path = Path("graph_visualization.png")
    output_path.write_bytes(png_data)
    print(f"Graph visualization saved to {output_path}")
    
    # Also print mermaid text representation
    mermaid_text = graph.get_graph().draw_mermaid()
    print("\nMermaid diagram text:")
    print("=" * 50)
    print(mermaid_text)

