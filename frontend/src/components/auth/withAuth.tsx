'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const withAuth = (WrappedComponent: React.ComponentType) => {
	const Wrapper = (props: any) => {
		const router = useRouter();
		const [isValidating, setIsValidating] = useState(true);

		useEffect(() => {
			const validateAuth = () => {
				const token = localStorage.getItem('auth_token');
				const tokenExpiry = localStorage.getItem('auth_token_expiry');

				if (!token) {
					router.push('/login');
					return;
				}

				if (tokenExpiry && new Date(tokenExpiry) < new Date()) {
					localStorage.removeItem('auth_token');
					localStorage.removeItem('auth_token_expiry');
					router.push('/login');
					return;
				}

				setIsValidating(false);
			};

			validateAuth();
		}, [router]);

		if (isValidating) {
			return (
				<div className="min-h-screen flex items-center justify-center">
					<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
				</div>
			);
		}

		return <WrappedComponent {...props} />;
	};

	return Wrapper;
};

export default withAuth;
