import { render } from '@testing-library/react';
import { axe } from 'jest-axe';

import { ApplicationCard, type Application } from '../ApplicationCard';

const baseApplication: Application = {
    id: 101,
    user_id: 1,
    job_id: 5001,
    status: 'Applied',
    applied_date: '2024-11-10T12:00:00Z',
    response_date: null,
    interview_date: '2024-11-15T15:30:00Z',
    offer_date: null,
    notes: 'Waiting for recruiter feedback regarding take-home exercise.',
    interview_feedback: null,
    follow_up_date: null,
    created_at: '2024-11-05T09:00:00Z',
    updated_at: '2024-11-10T12:30:00Z',
    job_title: 'Senior Frontend Engineer',
    company_name: 'Acme Corp',
    job_location: 'Berlin, Germany',
};

describe('ApplicationCard accessibility', () => {
    it.each([
        ['default' as const],
        ['compact' as const],
        ['detailed' as const],
    ])('renders the %s variant without axe violations', async (variant) => {
        const { container } = render(
            <ApplicationCard
                application={baseApplication}
                variant={variant}
                isSelected
                onSelect={() => undefined}
            />,
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('handles cards without interactive props accessibly', async () => {
        const minimalApplication: Application = {
            ...baseApplication,
            interview_date: null,
            notes: null,
        };

        const { container } = render(
            <ApplicationCard application={minimalApplication} variant="default" />,
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });
});
