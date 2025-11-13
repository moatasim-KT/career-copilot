# onboardingReducer

**File:** `frontend/src/components/onboarding/OnboardingWizard.tsx`

## Description

State reducer



## Props


### `data`
- **Type:** `any`
- **Required:** Yes




### `onChange`
- **Type:** `(data: any) => void`
- **Required:** Yes




### `onNext`
- **Type:** `() => void`
- **Required:** No




### `onBack`
- **Type:** `() => void`
- **Required:** No




### `onSkip`
- **Type:** `() => void`
- **Required:** No




### `isOpen`
- **Type:** `boolean`
- **Required:** Yes




### `onClose`
- **Type:** `() => void`
- **Required:** Yes




### `onComplete`
- **Type:** `() => void`
- **Required:** No




### `startStep`
- **Type:** `number`
- **Required:** No




### `state`
- **Type:** `OnboardingState`
- **Required:** Yes




### `action`
- **Type:** `StateAction`
- **Required:** Yes





## Dependencies

- `./steps/WelcomeStep`
- `./steps/SkillsStep`
- `./steps/ResumeStep`
- `./steps/PreferencesStep`
- `./steps/FeatureTourStep`
- `./steps/CompletionStep`




---
*Auto-generated from component source*
