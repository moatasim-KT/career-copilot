
import React, { useContext } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { FileUpload } from '@/components/ui/FileUpload';
import { AuthContext } from '@/context/AuthContext'; // Assuming AuthContext exists

const welcomeSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  jobTitle: z.string().min(1, 'Job title is required'),
  yearsOfExperience: z.string().min(1, 'Years of experience is required'),
});

type WelcomeFormData = z.infer<typeof welcomeSchema>;

interface WelcomeStepProps {
  data: WelcomeFormData;
  onChange: (data: Partial<WelcomeFormData>) => void;
}

const WelcomeStep: React.FC<WelcomeStepProps> = ({ data, onChange }) => {
  const { user } = useContext(AuthContext);
  const { register, handleSubmit, formState: { errors } } = useForm<WelcomeFormData>({
    resolver: zodResolver(welcomeSchema),
    defaultValues: {
      ...data,
      email: user?.email || data.email,
    },
  });

  const onSubmit = (formData: WelcomeFormData) => {
    onChange(formData);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold">Welcome to Career Copilot</h2>
      <p className="mt-2 text-gray-600">Your AI-powered copilot for navigating the European tech job market. Let's build your profile to find your dream job.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6">
        <Input
          label="Full Name"
          {...register('name')}
          error={errors.name?.message}
        />
        <Input
          label="Email Address"
          type="email"
          {...register('email')}
          error={errors.email?.message}
        />
        <Input
          label="Job Title"
          {...register('jobTitle')}
          error={errors.jobTitle?.message}
        />
        <Select
          label="Years of Experience"
          {...register('yearsOfExperience')}
          error={errors.yearsOfExperience?.message}
        >
          <option value="">Select...</option>
          <option value="0-1">0-1 years</option>
          <option value="1-3">1-3 years</option>
          <option value="3-5">3-5 years</option>
          <option value="5-10">5-10 years</option>
          <option value="10+">10+ years</option>
        </Select>
        <FileUpload
          label="Profile Photo (Optional)"
          onUpload={(file) => {
            // Handle file upload
          }}
        />
      </form>
    </div>
  );
};

export default WelcomeStep;
