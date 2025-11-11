import type { Meta, StoryObj } from '@storybook/react';
import {
  OptimizedImage,
  OptimizedAvatar,
  OptimizedLogo,
  OptimizedThumbnail,
} from '../OptimizedImage';

const meta: Meta<typeof OptimizedImage> = {
  title: 'UI/OptimizedImage',
  component: OptimizedImage,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Optimized image component with automatic WebP conversion, lazy loading, and error handling.',
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof OptimizedImage>;

export const Default: Story = {
  args: {
    src: '/images/placeholder.svg',
    alt: 'Placeholder image',
    width: 400,
    height: 300,
  },
};

export const WithAspectRatio: Story = {
  args: {
    src: '/images/placeholder.svg',
    alt: 'Square image',
    width: 300,
    height: 300,
    aspectRatio: 'square',
  },
};

export const VideoAspectRatio: Story = {
  args: {
    src: '/images/placeholder.svg',
    alt: 'Video aspect ratio',
    width: 640,
    height: 360,
    aspectRatio: 'video',
  },
};

export const WithFill: Story = {
  render: () => (
    <div className="relative w-96 h-64 border border-neutral-300 dark:border-neutral-700">
      <OptimizedImage
        src="/images/placeholder.svg"
        alt="Fill container"
        fill
        objectFit="cover"
      />
    </div>
  ),
};

export const WithPriority: Story = {
  args: {
    src: '/images/placeholder.svg',
    alt: 'Priority image',
    width: 400,
    height: 300,
    priority: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Use priority for above-the-fold images to load them immediately.',
      },
    },
  },
};

export const WithFallback: Story = {
  args: {
    src: '/non-existent-image.jpg',
    alt: 'Image with fallback',
    width: 400,
    height: 300,
    fallbackSrc: '/images/placeholder.svg',
  },
  parameters: {
    docs: {
      description: {
        story: 'Automatically shows fallback image when the main image fails to load.',
      },
    },
  },
};

// Avatar Stories
const avatarMeta: Meta<typeof OptimizedAvatar> = {
  title: 'UI/OptimizedImage/Avatar',
  component: OptimizedAvatar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export const Avatar: StoryObj<typeof OptimizedAvatar> = {
  ...avatarMeta,
  args: {
    src: '/images/default-avatar.svg',
    alt: 'User avatar',
    size: 40,
  },
};

export const LargeAvatar: StoryObj<typeof OptimizedAvatar> = {
  ...avatarMeta,
  args: {
    src: '/images/default-avatar.svg',
    alt: 'Large avatar',
    size: 80,
  },
};

export const SmallAvatar: StoryObj<typeof OptimizedAvatar> = {
  ...avatarMeta,
  args: {
    src: '/images/default-avatar.svg',
    alt: 'Small avatar',
    size: 24,
  },
};

export const AvatarGrid: StoryObj<typeof OptimizedAvatar> = {
  ...avatarMeta,
  render: () => (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((i) => (
        <OptimizedAvatar
          key={i}
          src="/images/default-avatar.svg"
          alt={`User ${i}`}
          size={40}
        />
      ))}
    </div>
  ),
};

// Logo Stories
const logoMeta: Meta<typeof OptimizedLogo> = {
  title: 'UI/OptimizedImage/Logo',
  component: OptimizedLogo,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export const Logo: StoryObj<typeof OptimizedLogo> = {
  ...logoMeta,
  args: {
    src: '/next.svg',
    alt: 'Next.js Logo',
    width: 120,
    height: 40,
  },
};

export const LargeLogo: StoryObj<typeof OptimizedLogo> = {
  ...logoMeta,
  args: {
    src: '/next.svg',
    alt: 'Large logo',
    width: 180,
    height: 60,
  },
};

// Thumbnail Stories
const thumbnailMeta: Meta<typeof OptimizedThumbnail> = {
  title: 'UI/OptimizedImage/Thumbnail',
  component: OptimizedThumbnail,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export const Thumbnail: StoryObj<typeof OptimizedThumbnail> = {
  ...thumbnailMeta,
  args: {
    src: '/images/placeholder.svg',
    alt: 'Thumbnail',
    size: 80,
  },
};

export const LargeThumbnail: StoryObj<typeof OptimizedThumbnail> = {
  ...thumbnailMeta,
  args: {
    src: '/images/placeholder.svg',
    alt: 'Large thumbnail',
    size: 120,
  },
};

export const ThumbnailGrid: StoryObj<typeof OptimizedThumbnail> = {
  ...thumbnailMeta,
  render: () => (
    <div className="grid grid-cols-3 gap-4">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <OptimizedThumbnail
          key={i}
          src="/images/placeholder.svg"
          alt={`Thumbnail ${i}`}
          size={100}
        />
      ))}
    </div>
  ),
};

// Responsive Examples
export const ResponsiveHero: Story = {
  render: () => (
    <div className="w-full max-w-4xl">
      <div className="relative w-full h-96">
        <OptimizedImage
          src="/images/placeholder.svg"
          alt="Hero image"
          fill
          objectFit="cover"
          priority
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <h1 className="text-4xl font-bold text-white">Hero Section</h1>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Responsive hero image with overlay content.',
      },
    },
  },
};

export const CardWithImage: Story = {
  render: () => (
    <div className="w-80 rounded-lg border border-neutral-200 dark:border-neutral-800 overflow-hidden">
      <OptimizedImage
        src="/images/placeholder.svg"
        alt="Card image"
        width={320}
        height={180}
        aspectRatio="video"
      />
      <div className="p-4">
        <h3 className="text-lg font-semibold mb-2">Card Title</h3>
        <p className="text-neutral-600 dark:text-neutral-400">
          Card description with optimized image above.
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card component with optimized image.',
      },
    },
  },
};

export const ImageGallery: Story = {
  render: () => (
    <div className="grid grid-cols-4 gap-4 max-w-4xl">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="relative aspect-square">
          <OptimizedImage
            src="/images/placeholder.svg"
            alt={`Gallery image ${i}`}
            fill
            objectFit="cover"
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 25vw, 200px"
          />
        </div>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Responsive image gallery with optimized loading.',
      },
    },
  },
};
