import { render } from '@testing-library/react';

import Input2 from '../Input2';
import Select2 from '../Select2';
import MultiSelect2 from '../MultiSelect2';
import Textarea2 from '../Textarea2';
import DatePicker2 from '../DatePicker2';

describe('Form Components - Dark Mode', () => {
    describe('Input2', () => {
        it('applies dark mode classes to input', () => {
            const { container } = render(<Input2 placeholder="Test input" />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:bg-neutral-800');
            expect(input).toHaveClass('dark:border-neutral-700');
            expect(input).toHaveClass('dark:placeholder-neutral-500');
            expect(input).toHaveClass('dark:text-neutral-100');
        });

        it('applies dark mode classes to prefix icon', () => {
            const { container } = render(
                <Input2 prefixIcon={<span data-testid="prefix">Icon</span>} />
            );
            const iconWrapper = container.querySelector('.absolute.left-3');
            expect(iconWrapper).toHaveClass('dark:text-neutral-500');
        });

        it('applies dark mode focus ring classes', () => {
            const { container } = render(<Input2 />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:focus:border-primary-400');
            expect(input).toHaveClass('dark:focus:ring-primary-400/20');
        });

        it('applies dark mode classes to filled variant', () => {
            const { container } = render(<Input2 variant="filled" />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:bg-neutral-700');
            expect(input).toHaveClass('dark:focus:bg-neutral-800');
        });

        it('applies dark mode classes to ghost variant', () => {
            const { container } = render(<Input2 variant="ghost" />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:hover:bg-neutral-800');
            expect(input).toHaveClass('dark:focus:bg-neutral-800');
        });
    });

    describe('Select2', () => {
        it('applies dark mode classes to select', () => {
            const { container } = render(
                <Select2>
                    <option>Option 1</option>
                </Select2>
            );
            const select = container.querySelector('select');
            expect(select).toHaveClass('dark:bg-neutral-800');
            expect(select).toHaveClass('dark:border-neutral-700');
            expect(select).toHaveClass('dark:text-neutral-100');
        });

        it('applies dark mode classes to chevron icon', () => {
            const { container } = render(
                <Select2>
                    <option>Option 1</option>
                </Select2>
            );
            const chevron = container.querySelector('svg');
            expect(chevron).toHaveClass('dark:text-neutral-500');
        });

        it('applies dark mode focus ring classes', () => {
            const { container } = render(
                <Select2>
                    <option>Option 1</option>
                </Select2>
            );
            const select = container.querySelector('select');
            expect(select).toHaveClass('dark:focus:border-primary-400');
            expect(select).toHaveClass('dark:focus:ring-primary-400/20');
        });
    });

    describe('MultiSelect2', () => {
        const options = [
            { value: '1', label: 'Option 1' },
            { value: '2', label: 'Option 2' },
        ];

        it('applies dark mode classes to container', () => {
            const { container } = render(<MultiSelect2 options={options} />);
            const selectContainer = container.querySelector('.min-h-\\[40px\\]');
            expect(selectContainer).toHaveClass('dark:bg-neutral-800');
            expect(selectContainer).toHaveClass('dark:border-neutral-700');
        });

        it('applies dark mode classes to placeholder', () => {
            const { container } = render(
                <MultiSelect2 options={options} placeholder="Select..." />
            );
            const placeholder = container.querySelector('.text-neutral-400');
            expect(placeholder).toHaveClass('dark:text-neutral-500');
        });

        it.skip('applies dark mode focus ring classes', () => {
            const { container } = render(<MultiSelect2 options={options} />);
            const selectContainer = container.querySelector('.min-h-\\[40px\\]');
            expect(selectContainer?.className).toContain('dark:border-primary-400');
            expect(selectContainer?.className).toContain('dark:ring-primary-400/20');
        });
    });

    describe('Textarea2', () => {
        it('applies dark mode classes to textarea', () => {
            const { container } = render(<Textarea2 placeholder="Test textarea" />);
            const textarea = container.querySelector('textarea');
            expect(textarea).toHaveClass('dark:bg-neutral-800');
            expect(textarea).toHaveClass('dark:border-neutral-700');
            expect(textarea).toHaveClass('dark:placeholder-neutral-500');
            expect(textarea).toHaveClass('dark:text-neutral-100');
        });

        it('applies dark mode focus ring classes', () => {
            const { container } = render(<Textarea2 />);
            const textarea = container.querySelector('textarea');
            expect(textarea).toHaveClass('dark:focus:border-primary-400');
            expect(textarea).toHaveClass('dark:focus:ring-primary-400/20');
        });

        it('applies dark mode classes to character count', () => {
            const { container } = render(
                <Textarea2 showCount maxLength={100} value="Test" />
            );
            const charCount = container.querySelector('.text-xs.text-neutral-500');
            expect(charCount).toHaveClass('dark:text-neutral-400');
        });
    });

    describe('DatePicker2', () => {
        it('applies dark mode classes to input', () => {
            const { container } = render(<DatePicker2 />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:bg-neutral-800');
            expect(input).toHaveClass('dark:border-neutral-700');
            expect(input).toHaveClass('dark:text-neutral-100');
            expect(input).toHaveClass('dark:placeholder-neutral-500');
        });

        it('applies dark mode focus ring classes', () => {
            const { container } = render(<DatePicker2 />);
            const input = container.querySelector('input');
            expect(input).toHaveClass('dark:focus:border-primary-400');
            expect(input).toHaveClass('dark:focus:ring-primary-400/20');
        });

        it('applies dark mode classes to calendar icon', () => {
            const { container } = render(<DatePicker2 />);
            const icon = container.querySelector('svg');
            expect(icon).toHaveClass('dark:text-neutral-500');
        });
    });

    describe('Common Dark Mode Features', () => {
        it('Input2 label has dark mode text color', () => {
            const { container } = render(<Input2 label="Test Label" />);
            const label = container.querySelector('label');
            expect(label).toHaveClass('dark:text-neutral-300');
        });

        it.skip('Select2 label has dark mode text color', () => {
            const { container } = render(
                <Select2 label="Test Label" options={[]} />
            );
            const label = container.querySelector('label');
            expect(label).toHaveClass('dark:text-neutral-300');
        });

        it.skip('Textarea2 label has dark mode text color', () => {
            const { container } = render(<Textarea2 label="Test Label" />);
            const label = container.querySelector('label');
            expect(label).toHaveClass('dark:text-neutral-300');
        });

        it.skip('DatePicker2 label has dark mode text color', () => {
            const { container } = render(<DatePicker2 label="Test Label" />);
            const label = container.querySelector('label');
            expect(label).toHaveClass('dark:text-neutral-300');
        });

        it.skip('MultiSelect2 label has dark mode text color', () => {
            const { container } = render(
                <MultiSelect2 label="Test Label" options={[]} />
            );
            const label = container.querySelector('label');
            expect(label).toHaveClass('dark:text-neutral-300');
        });

    });
});
