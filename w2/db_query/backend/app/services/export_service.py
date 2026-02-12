"""Export service for formatting query results."""

import csv
import json
import io
from typing import Any
from datetime import datetime


class ExportService:
    """Service for exporting query results to different formats."""

    @staticmethod
    def to_csv(data: list[dict[str, Any]]) -> bytes:
        """Convert data to CSV format with GBK encoding for Windows Excel compatibility."""
        if not data:
            return b""
        
        output = io.StringIO()
        
        # Get column names from first row
        fieldnames = list(data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            # Convert any non-string values to strings
            cleaned_row = {k: str(v) if v is not None else '' for k, v in row.items()}
            writer.writerow(cleaned_row)
        
        # For Windows Excel, use GBK encoding which handles Chinese characters better
        # GBK is the default encoding for Chinese Windows systems
        csv_content = output.getvalue()
        try:
            return csv_content.encode('gbk')
        except UnicodeEncodeError:
            # Fallback to UTF-8 with BOM if GBK encoding fails
            return '\ufeff'.encode('utf-8') + csv_content.encode('utf-8')

    @staticmethod
    def to_json(data: list[dict[str, Any]]) -> bytes:
        """Convert data to JSON format."""
        json_content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
        return json_content.encode('utf-8')

    @staticmethod
    def generate_filename(format: str, custom_name: str | None = None) -> str:
        """Generate a filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if custom_name:
            return f"{custom_name}.{format}"
        else:
            return f"export_{timestamp}.{format}"

    def export_data(self, data: list[dict[str, Any]], format: str, filename: str | None = None) -> tuple[bytes, str]:
        """Export data to the specified format.
        
        Returns:
            tuple: (exported_content_bytes, filename)
        """
        if format == "csv":
            content = self.to_csv(data)
        elif format == "json":
            content = self.to_json(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        generated_filename = self.generate_filename(format, filename)
        
        return content, generated_filename
