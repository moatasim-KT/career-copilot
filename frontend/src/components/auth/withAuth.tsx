'use client';

import type { ComponentType } from 'react';

const withAuth = <P extends object>(WrappedComponent: ComponentType<P>) => {
	const Wrapper = (props: P) => <WrappedComponent {...props} />;

	Wrapper.displayName = `WithAuth(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;

	return Wrapper;
};

export default withAuth;
