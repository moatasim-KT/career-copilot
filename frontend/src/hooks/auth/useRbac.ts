
import { useEffect, useState } from 'react';
import { getUser, hasRole, Role, User } from '../../lib/auth/rbac';

export function useRbac(roles: Role[]) {
  const [user, setUser] = useState<User | null>(null);
  const [isAllowed, setIsAllowed] = useState(false);

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);
    setIsAllowed(hasRole(currentUser, roles));
  }, [roles]);

  return { user, isAllowed };
}
