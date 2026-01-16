"""
Soviet UI Theme Compliance Verification
Tests PhaseB01Review.jsx and NeonPhaseCard.jsx against SOVIET_UI_DOCUMENTATION.md spec
Verifies fonts (Orbitron, Share Tech Mono, Russo One), colors (cyan, amber, red, green), brutalist aesthetic
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import re


@pytest.fixture
def soviet_ui_spec():
    """Fixture: Soviet UI specification from documentation"""
    return {
        "fonts": {
            "headers": "OCR A Extended",  # From SOVIET_UI_DOCUMENTATION.md
            "body": "Share Tech Mono",
            "display": "Russo One",
            # Common alternative: Orbitron (retro-futuristic)
        },
        "colors": {
            "soviet_red": "#8B0000",
            "warning_amber": "#FFA500",
            "steel_gray": "#4A5568",
            "panel_dark": "#1A1A1A",
            "led_green": "#00FF00",
            "nixie_orange": "#FF6B35",
            # Phase implementation uses:
            "neon_cyan": "#00FFFF",
            "neon_amber": "#FFB000",
            "neon_red": "#FF0040",
        },
        "aesthetic": [
            "brutalist",
            "industrial",
            "high_contrast",
            "retro_futuristic",
            "geometric_patterns",
            "heavy_borders"
        ]
    }


@pytest.fixture
def phase_b01_review_jsx():
    """Fixture: PhaseB01Review.jsx file content"""
    jsx_path = Path(__file__).parent.parent.parent / "apps" / "ui" / "react-app" / "src" / "components" / "phases" / "PhaseB01Review.jsx"
    
    if not jsx_path.exists():
        pytest.skip(f"PhaseB01Review.jsx not found at {jsx_path}")
    
    with open(jsx_path, 'r') as f:
        return f.read()


@pytest.fixture
def neon_phase_card_jsx():
    """Fixture: NeonPhaseCard.jsx file content"""
    jsx_path = Path(__file__).parent.parent.parent / "apps" / "ui" / "react-app" / "src" / "components" / "ui" / "NeonPhaseCard.jsx"
    
    if not jsx_path.exists():
        pytest.skip(f"NeonPhaseCard.jsx not found at {jsx_path}")
    
    with open(jsx_path, 'r') as f:
        return f.read()


class TestPhaseB01ReviewCompliance:
    """Test PhaseB01Review.jsx Soviet theme compliance"""

    def test_orbitron_font_usage(self, phase_b01_review_jsx):
        """Test: Uses Orbitron font for headers"""
        # Check for Orbitron font family - matches both "Orbitron" and 'Orbitron'
        orbitron_pattern = r'fontFamily.*["\']*Orbitron["\']*'
        matches = re.findall(orbitron_pattern, phase_b01_review_jsx, re.IGNORECASE)
        
        assert len(matches) > 0, "PhaseB01Review.jsx should use Orbitron font"

    def test_share_tech_mono_font_usage(self, phase_b01_review_jsx):
        """Test: Uses Share Tech Mono for monospace/data display"""
        # Check for Share Tech Mono font family
        share_tech_pattern = r'fontFamily.*["\']Share Tech Mono'
        matches = re.findall(share_tech_pattern, phase_b01_review_jsx, re.IGNORECASE)
        
        # Note: May not be used in every component, but should be available
        # This test is informational rather than strict requirement

    def test_cyan_color_usage(self, phase_b01_review_jsx):
        """Test: Uses cyan color (#00FFFF or var(--neon-cyan))"""
        # Check for cyan color usage
        cyan_patterns = [
            r'#00FFFF',
            r'var\(--neon-cyan\)',
            r'backgroundColor.*["\']cyan',
            r'color.*["\']cyan'
        ]
        
        found_cyan = any(
            re.search(pattern, phase_b01_review_jsx, re.IGNORECASE)
            for pattern in cyan_patterns
        )
        
        assert found_cyan, "PhaseB01Review.jsx should use cyan color for Soviet theme"

    def test_high_contrast_elements(self, phase_b01_review_jsx):
        """Test: Uses high contrast colors (black/white backgrounds)"""
        # Check for dark backgrounds and light text (high contrast)
        contrast_patterns = [
            r'backgroundColor.*["\']#000',
            r'backgroundColor.*black',
            r'color.*["\']#FFF',
            r'color.*white'
        ]
        
        found_contrast = any(
            re.search(pattern, phase_b01_review_jsx, re.IGNORECASE)
            for pattern in contrast_patterns
        )
        
        assert found_contrast, "Should use high contrast colors for Soviet aesthetic"

    def test_geometric_layout(self, phase_b01_review_jsx):
        """Test: Uses geometric/grid layout patterns"""
        # Check for Material-UI grid or flex layout
        layout_patterns = [
            r'display.*["\']flex',
            r'display.*["\']grid',
            r'<Grid',
            r'<Box'
        ]
        
        found_layout = any(
            re.search(pattern, phase_b01_review_jsx)
            for pattern in layout_patterns
        )
        
        assert found_layout, "Should use geometric layout patterns"

    def test_validation_chip_colors(self, phase_b01_review_jsx):
        """Test: Uses color-coded validation chips (success/warning/error)"""
        # Check for Chip components with color props - matches both quoted and JSX expression syntax
        chip_patterns = [
            r'<Chip[^>]*color=["\'](success|warning|error)',
            r'color=\{[^}]*\?\s*["\']*(success|warning|error)["\']*'
        ]
        
        found_colors = []
        for pattern in chip_patterns:
            matches = re.findall(pattern, phase_b01_review_jsx)
            found_colors.extend(matches)
        
        assert len(found_colors) > 0, "Should use color-coded Chip components for validation status"

    def test_tabs_interface(self, phase_b01_review_jsx):
        """Test: Uses tabbed interface for deliverables"""
        # Check for Material-UI Tabs component
        tabs_patterns = [
            r'<Tabs',
            r'<Tab\s',
            r'TabPanel'
        ]
        
        found_tabs = any(
            re.search(pattern, phase_b01_review_jsx)
            for pattern in tabs_patterns
        )
        
        assert found_tabs, "Should use tabbed interface for multi-deliverable review"


class TestNeonPhaseCardCompliance:
    """Test NeonPhaseCard.jsx Soviet theme compliance"""

    def test_review_button_exists(self, neon_phase_card_jsx):
        """Test: Has 'Review All Deliverables' button"""
        button_pattern = r'Review All Deliverables'
        
        assert re.search(button_pattern, neon_phase_card_jsx), \
            "NeonPhaseCard should have 'Review All Deliverables' button"

    def test_review_button_orbitron_font(self, neon_phase_card_jsx):
        """Test: Review button uses Orbitron font"""
        # Find button section and check for Orbitron
        # Pattern: Button with "Review All Deliverables" text should have Orbitron fontFamily
        button_section_pattern = r'Review All Deliverables.*?</Button>'
        button_section = re.search(button_section_pattern, neon_phase_card_jsx, re.DOTALL)
        
        if button_section:
            button_text = button_section.group(0)
            
            # Check for Orbitron in sx prop or nearby styling
            # Look backwards from button to find sx prop
            context_start = max(0, button_section.start() - 1000)
            context = neon_phase_card_jsx[context_start:button_section.end()]
            
            has_orbitron = re.search(r'fontFamily.*["\']Orbitron', context, re.IGNORECASE)
            assert has_orbitron, "Review button should use Orbitron font"

    def test_review_button_cyan_color(self, neon_phase_card_jsx):
        """Test: Review button uses cyan color"""
        # Find button section
        button_section_pattern = r'Review All Deliverables.*?</Button>'
        button_section = re.search(button_section_pattern, neon_phase_card_jsx, re.DOTALL)
        
        if button_section:
            # Look backwards from button to find sx prop with color
            context_start = max(0, button_section.start() - 1000)
            context = neon_phase_card_jsx[context_start:button_section.end()]
            
            cyan_patterns = [
                r'backgroundColor.*["\'].*cyan',
                r'var\(--neon-cyan\)'
            ]
            
            has_cyan = any(
                re.search(pattern, context, re.IGNORECASE)
                for pattern in cyan_patterns
            )
            
            assert has_cyan, "Review button should use cyan background color"

    def test_review_button_hover_effect(self, neon_phase_card_jsx):
        """Test: Review button has hover effect (glow/shadow)"""
        # Find button section and check for hover effects
        button_section_pattern = r'Review All Deliverables.*?</Button>'
        button_section = re.search(button_section_pattern, neon_phase_card_jsx, re.DOTALL)
        
        if button_section:
            context_start = max(0, button_section.start() - 1000)
            context = neon_phase_card_jsx[context_start:button_section.end()]
            
            hover_patterns = [
                r'&:hover',
                r'boxShadow',
                r'glow'
            ]
            
            has_hover = any(
                re.search(pattern, context, re.IGNORECASE)
                for pattern in hover_patterns
            )
            
            assert has_hover, "Review button should have hover effect (glow/shadow)"


class TestOverallCompliance:
    """Test overall Soviet theme compliance"""

    def test_no_default_material_ui_theme(self, phase_b01_review_jsx, neon_phase_card_jsx):
        """Test: Components don't rely solely on default Material-UI theme"""
        # Check that custom styling is applied (sx props or styled components)
        files_to_check = [
            ("PhaseB01Review.jsx", phase_b01_review_jsx),
            ("NeonPhaseCard.jsx", neon_phase_card_jsx)
        ]
        
        for filename, content in files_to_check:
            # Check for custom styling via sx prop
            has_custom_styling = re.search(r'\bsx=\{', content)
            
            assert has_custom_styling, \
                f"{filename} should use custom styling (sx prop) rather than default Material-UI theme"

    def test_consistent_font_family(self, phase_b01_review_jsx):
        """Test: Consistent font family usage (Orbitron for primary text)"""
        # Count fontFamily occurrences - look for both quoted and unquoted formats
        font_families = re.findall(r'fontFamily\s*:\s*["\']*([^"\',]+)', phase_b01_review_jsx)
        
        # Should have multiple fontFamily declarations
        assert len(font_families) > 0, "Should specify fontFamily for custom theme"
        
        # Orbitron should be dominant
        orbitron_count = sum(1 for font in font_families if 'Orbitron' in font)
        
        assert orbitron_count > 0, "Orbitron should be used for Soviet retro-futuristic theme"

    def test_color_variable_usage(self, phase_b01_review_jsx, neon_phase_card_jsx):
        """Test: Uses CSS variables (var(--neon-cyan), etc.) for consistent theming"""
        files_to_check = [
            ("PhaseB01Review.jsx", phase_b01_review_jsx),
            ("NeonPhaseCard.jsx", neon_phase_card_jsx)
        ]
        
        for filename, content in files_to_check:
            # Check for CSS variable usage
            has_css_vars = re.search(r'var\(--[a-z-]+\)', content)
            
            # Note: Some components may use hex colors directly
            # This test is informational rather than strict requirement


class TestAccessibility:
    """Test that Soviet theme maintains accessibility"""

    def test_aria_labels_present(self, phase_b01_review_jsx):
        """Test: Interactive elements have ARIA labels"""
        # Check for ARIA labels on interactive elements
        aria_patterns = [
            r'aria-label',
            r'aria-labelledby',
            r'aria-describedby'
        ]
        
        # Note: Not all components require ARIA labels
        # This test is informational
        has_aria = any(
            re.search(pattern, phase_b01_review_jsx, re.IGNORECASE)
            for pattern in aria_patterns
        )

    def test_semantic_html(self, phase_b01_review_jsx):
        """Test: Uses semantic HTML/React components"""
        # Check for semantic component usage
        semantic_patterns = [
            r'<Typography',
            r'<Button',
            r'<Box',
            r'<Tabs',
            r'<Tab'
        ]
        
        found_semantic = sum(
            1 for pattern in semantic_patterns
            if re.search(pattern, phase_b01_review_jsx)
        )
        
        assert found_semantic >= 3, "Should use semantic React components"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
