import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { Sparkles } from 'lucide-react';

import Button2 from '../Button2';

describe('Button2 accessibility', () => {
    it.each([
        ['primary' as const],
        ['secondary' as const],
        ['outline' as const],
        ['ghost' as const],
        ['gradient' as const],
    ])('renders the %s variant without axe violations', async (variant) => {
        const { container } = render(<Button2 variant={variant}>Submit</Button2>);

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('announces loading state politely', async () => {
        const { container } = render(
            <Button2 loading loadingText="Saving" icon={<Sparkles aria-hidden="true" focusable="false" />}>
                Save
            </Button2>,
        );

        const button = screen.getByRole('button', { name: /saving/i });
        expect(button).toHaveAttribute('aria-busy', 'true');

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });
});
