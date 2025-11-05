/**
 * Loading component with optional text
 * Used as a fallback for lazy-loaded components
 */
export default function Loading({
    text = 'Loading...',
    size = 'md',
    fullScreen = false,
}: {
    text?: string;
    size?: 'sm' | 'md' | 'lg';
    fullScreen?: boolean;
}) {
    const sizeClasses = {
        sm: 'h-6 w-6',
        md: 'h-12 w-12',
        lg: 'h-16 w-16',
    };

    const containerClasses = fullScreen
        ? 'flex flex-col items-center justify-center min-h-screen'
        : 'flex flex-col items-center justify-center p-8';

    return (
        <div className={containerClasses}>
            <div
                className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`}
                role="status"
                aria-label={text}
            ></div>
            {text && (
                <p className="mt-4 text-sm text-gray-600">{text}</p>
            )}
        </div>
    );
}
