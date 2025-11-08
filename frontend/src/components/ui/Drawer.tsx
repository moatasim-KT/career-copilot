import { X } from 'lucide-react';
import React from 'react';

export interface DrawerProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    position?: 'left' | 'right' | 'top' | 'bottom';
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
    children: React.ReactNode;
}

const positionClasses = {
    left: 'left-0 top-0 h-full',
    right: 'right-0 top-0 h-full',
    top: 'top-0 left-0 w-full',
    bottom: 'bottom-0 left-0 w-full',
};

const sizeClasses = {
    sm: 'w-64',
    md: 'w-96',
    lg: 'w-[32rem]',
    xl: 'w-[48rem]',
    full: 'w-full h-full',
};

export default function Drawer({
    isOpen,
    onClose,
    title,
    position = 'right',
    size = 'md',
    children,
}: DrawerProps) {
    if (!isOpen) return null;

    const posClass = positionClasses[position];
    const sizeClass = position === 'top' || position === 'bottom' ? 'h-96' : sizeClasses[size];

    return (
        <div className="fixed inset-0 z-50 flex">
            <div className="fixed inset-0 bg-black bg-opacity-40" onClick={onClose} />
            <div
                className={`fixed bg-white shadow-xl transition-transform duration-300 ${posClass} ${sizeClass} rounded-lg`}
                style={{
                    transform: isOpen ? 'translateX(0)' : position === 'right' ? 'translateX(100%)' : 'translateX(-100%)',
                }}
            >
                <div className="flex items-center justify-between p-4 border-b">
                    {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-4">{children}</div>
            </div>
        </div>
    );
}
