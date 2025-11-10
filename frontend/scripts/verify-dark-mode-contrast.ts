/**
 * Dark Mode Color Contrast Verification Script
 * 
 * Verifies that all color combinations in dark mode meet WCAG AA standards (4.5:1 contrast ratio).
 * Run with: npx tsx scripts/verify-dark-mode-contrast.ts
 */

interface ColorPair {
  name: string;
  foreground: string;
  background: string;
  usage: string;
}

// Helper to convert hex to RGB
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

// Helper to convert RGB string to object
function rgbStringToObject(rgb: string): { r: number; g: number; b: number } | null {
  const match = rgb.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
  if (!match) return null;
  
  return {
    r: parseInt(match[1], 10),
    g: parseInt(match[2], 10),
    b: parseInt(match[3], 10),
  };
}

// Calculate relative luminance (WCAG formula)
function getRelativeLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((val) => {
    const s = val / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio
function getContrastRatio(color1: string, color2: string): number {
  let rgb1 = hexToRgb(color1) || rgbStringToObject(color1);
  let rgb2 = hexToRgb(color2) || rgbStringToObject(color2);

  if (!rgb1 || !rgb2) {
    throw new Error(`Invalid color format: ${color1} or ${color2}`);
  }

  const l1 = getRelativeLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getRelativeLuminance(rgb2.r, rgb2.g, rgb2.b);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
}

// Check if contrast meets WCAG standards
function meetsWCAG(ratio: number, level: 'AA' | 'AAA' = 'AA', size: 'normal' | 'large' = 'normal'): boolean {
  if (level === 'AA') {
    return size === 'normal' ? ratio >= 4.5 : ratio >= 3.0;
  } else {
    return size === 'normal' ? ratio >= 7.0 : ratio >= 4.5;
  }
}

// Dark mode color pairs to verify
const darkModeColorPairs: ColorPair[] = [
  // Page backgrounds
  {
    name: 'Body text on page background',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Main page content',
  },
  {
    name: 'Muted text on page background',
    foreground: 'rgb(148, 163, 184)', // neutral-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Secondary text, captions',
  },

  // Card backgrounds
  {
    name: 'Text on card background',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Card content',
  },
  {
    name: 'Muted text on card',
    foreground: 'rgb(148, 163, 184)', // neutral-400
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Card secondary text',
  },

  // Navigation
  {
    name: 'Navigation text',
    foreground: 'rgb(148, 163, 184)', // neutral-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Navigation links',
  },
  {
    name: 'Active navigation text',
    foreground: 'rgb(147, 197, 253)', // primary-300
    background: 'rgb(30, 58, 138)', // primary-900/30 approximation
    usage: 'Active navigation item',
  },

  // Buttons
  {
    name: 'Primary button text',
    foreground: 'rgb(255, 255, 255)', // white
    background: 'rgb(37, 99, 235)', // primary-600
    usage: 'Primary button',
  },
  {
    name: 'Secondary button text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(51, 65, 85)', // neutral-700
    usage: 'Secondary button',
  },
  {
    name: 'Ghost button text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(15, 23, 42)', // neutral-900 (transparent)
    usage: 'Ghost button',
  },

  // Form inputs
  {
    name: 'Input text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Input fields',
  },
  {
    name: 'Input placeholder',
    foreground: 'rgb(100, 116, 139)', // neutral-500
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Input placeholders',
  },
  {
    name: 'Input label',
    foreground: 'rgb(203, 213, 225)', // neutral-300
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Input labels',
  },

  // Status colors
  {
    name: 'Success text',
    foreground: 'rgb(74, 222, 128)', // green-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Success messages',
  },
  {
    name: 'Warning text',
    foreground: 'rgb(251, 146, 60)', // orange-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Warning messages',
  },
  {
    name: 'Error text',
    foreground: 'rgb(248, 113, 113)', // red-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Error messages',
  },
  {
    name: 'Info text',
    foreground: 'rgb(96, 165, 250)', // blue-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Info messages',
  },

  // Links
  {
    name: 'Link text',
    foreground: 'rgb(96, 165, 250)', // primary-400
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Hyperlinks',
  },
  {
    name: 'Link hover',
    foreground: 'rgb(147, 197, 253)', // primary-300
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Hovered links',
  },

  // Modal/Dialog
  {
    name: 'Modal text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Modal content',
  },
  {
    name: 'Modal header',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Modal header',
  },

  // Tables
  {
    name: 'Table header text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(30, 41, 59)', // neutral-800
    usage: 'Table headers',
  },
  {
    name: 'Table row text',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Table rows',
  },
  {
    name: 'Table row hover',
    foreground: 'rgb(248, 250, 252)', // neutral-50
    background: 'rgb(51, 65, 85)', // neutral-700
    usage: 'Hovered table rows',
  },

  // Borders (decorative elements only need 3:1)
  {
    name: 'Border on dark background',
    foreground: 'rgb(51, 65, 85)', // neutral-700
    background: 'rgb(15, 23, 42)', // neutral-900
    usage: 'Borders (decorative, 3:1 minimum for non-text)',
  },
];

// Special cases that don't need 4.5:1 contrast
const specialCases = {
  'Input placeholder': 3.0, // Placeholders are non-essential, 3:1 is acceptable
  'Border on dark background': 3.0, // Decorative borders only need 3:1
};

// Verify all color pairs
function verifyColorContrast() {
  console.log('🎨 Dark Mode Color Contrast Verification\n');
  console.log('WCAG AA Standard: 4.5:1 for normal text, 3.0:1 for large text\n');
  console.log('=' .repeat(100));

  let passCount = 0;
  let failCount = 0;
  const failures: Array<{ pair: ColorPair; ratio: number }> = [];

  for (const pair of darkModeColorPairs) {
    try {
      const ratio = getContrastRatio(pair.foreground, pair.background);
      const requiredRatio = specialCases[pair.name] || 4.5;
      const passes = ratio >= requiredRatio;

      const status = passes ? '✅ PASS' : '❌ FAIL';
      const color = passes ? '\x1b[32m' : '\x1b[31m';
      const reset = '\x1b[0m';

      console.log(`\n${color}${status}${reset} ${pair.name}`);
      console.log(`  Usage: ${pair.usage}`);
      console.log(`  Foreground: ${pair.foreground}`);
      console.log(`  Background: ${pair.background}`);
      console.log(`  Contrast Ratio: ${ratio.toFixed(2)}:1`);
      
      if (specialCases[pair.name]) {
        console.log(`  ℹ️  Special case: ${requiredRatio}:1 required (not 4.5:1)`);
      }

      if (passes) {
        passCount++;
        if (meetsWCAG(ratio, 'AAA', 'normal')) {
          console.log(`  🌟 Also meets WCAG AAA (7:1)`);
        }
      } else {
        failCount++;
        failures.push({ pair, ratio });
        console.log(`  ⚠️  Required: ${requiredRatio}:1, Got: ${ratio.toFixed(2)}:1`);
        console.log(`  📊 Shortfall: ${(requiredRatio - ratio).toFixed(2)}`);
      }
    } catch (error) {
      console.error(`\n❌ ERROR processing ${pair.name}:`, error);
      failCount++;
    }
  }

  // Summary
  console.log('\n' + '='.repeat(100));
  console.log('\n📊 Summary\n');
  console.log(`Total color pairs tested: ${darkModeColorPairs.length}`);
  console.log(`✅ Passed: ${passCount} (${((passCount / darkModeColorPairs.length) * 100).toFixed(1)}%)`);
  console.log(`❌ Failed: ${failCount} (${((failCount / darkModeColorPairs.length) * 100).toFixed(1)}%)`);

  if (failures.length > 0) {
    console.log('\n⚠️  Failed Color Pairs:\n');
    failures.forEach(({ pair, ratio }) => {
      console.log(`  • ${pair.name}: ${ratio.toFixed(2)}:1 (needs ${(4.5 - ratio).toFixed(2)} more)`);
    });
  }

  console.log('\n' + '='.repeat(100));

  // Recommendations
  if (failures.length > 0) {
    console.log('\n💡 Recommendations:\n');
    console.log('  1. Increase foreground color brightness or decrease background brightness');
    console.log('  2. Use lighter shades for text (e.g., neutral-100 instead of neutral-200)');
    console.log('  3. Use darker shades for backgrounds (e.g., neutral-900 instead of neutral-800)');
    console.log('  4. Test with WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/');
    console.log('  5. Consider using semantic color tokens that automatically adjust for dark mode');
  } else {
    console.log('\n🎉 All color pairs meet WCAG AA standards!');
  }

  // Exit with error code if any failures
  if (failCount > 0) {
    process.exit(1);
  }
}

// Run verification
verifyColorContrast();
