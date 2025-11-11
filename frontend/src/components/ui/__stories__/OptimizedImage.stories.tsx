import type { Meta, StoryObj } from '@storybook/react';
import {
  OptimizedImage,
  OptimizedAvatar,
  OptimizedLogo,
  OptimizedThumbnail,
  RESPONSIVE_SIZES,
} from '../OptimizedImage';

const meta: Meta<typeof OptimizedImage> = {
  title: 'UI/OptimizedImage',
  component: OptimizedImage,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Optimized image component with automatic WebP/AVIF conversion, responsive sizing, lazy loading, and error handling. Supports preset responsive contexts for common layouts.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    responsiveContext: {
      control: 'select',
      options: ['auto', ...Object.keys(RESPONSIVE_SIZES)],
      description: 'Preset responsive sizes for common layouts',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'auto' },
      },
    },
  },
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

// Responsive Context Examples
export const ResponsiveContextHero: Story = {
  render: () => (
    <div className="w-full max-w-4xl">
      <div className="relative w-full h-96">
        <OptimizedImage
          src="/images/placeholder.svg"
          alt="Hero with responsive context"
          fill
          objectFit="cover"
          responsiveContext="hero"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <div className="text-center text-white">
            <h1 className="text-4xl font-bold mb-2">Responsive Hero</h1>
            <p className="text-sm opacity-80">Using responsiveContext="hero"</p>
          </div>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Hero image using the "hero" responsive context preset. Automatically applies: (max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
      },
    },
  },
};

export const ResponsiveContextCard: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="rounded-lg border border-neutral-200 dark:border-neutral-800 overflow-hidden">
          <div className="relative w-full h-48">
            <OptimizedImage
              src="/images/placeholder.svg"
              alt={`Card ${i}`}
              fill
              objectFit="cover"
              responsiveContext="card"
            />
          </div>
          <div className="p-4">
            <h3 className="text-lg font-semibold mb-2">Card {i}</h3>
            <p className="text-neutral-600 dark:text-neutral-400 text-sm">
              Using responsiveContext="card"
            </p>
          </div>
        </div>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card images using the "card" responsive context preset. Automatically applies: (max-width: 768px) 100vw, 50vw',
      },
    },
  },
};

export const ResponsiveContextGrid: Story = {
  render: () => (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-w-4xl">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="relative aspect-square rounded-lg overflow-hidden">
          <OptimizedImage
            src="/images/placeholder.svg"
            alt={`Grid item ${i}`}
            fill
            objectFit="cover"
            responsiveContext="grid"
          />
        </div>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Grid images using the "grid" responsive context preset. Automatically applies: (max-width: 640px) 100vw, (max-width: 1024px) 33vw, 25vw',
      },
    },
  },
};

export const ResponsiveContextBanner: Story = {
  render: () => (
    <div className="w-full max-w-6xl">
      <div className="relative w-full h-64">
        <OptimizedImage
          src="/images/placeholder.svg"
          alt="Banner"
          fill
          objectFit="cover"
          responsiveContext="banner"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-black/60 to-transparent">
          <div className="text-white text-left px-8">
            <h2 className="text-3xl font-bold mb-2">Banner Image</h2>
            <p className="text-sm opacity-90">Using responsiveContext="banner"</p>
          </div>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Banner image using the "banner" responsive context preset. Automatically applies: (max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px',
      },
    },
  },
};

export const ResponsiveContextContent: Story = {
  render: () => (
    <div className="max-w-3xl mx-auto prose dark:prose-invert">
      <h2>Article with Responsive Image</h2>
      <p>
        This is an example of an article with an embedded image using the content responsive context.
      </p>
      <div className="relative w-full h-96 my-8">
        <OptimizedImage
          src="/images/placeholder.svg"
          alt="Content image"
          fill
          objectFit="cover"
          responsiveContext="content"
        />
      </div>
      <p>
        The image automatically adapts to different screen sizes using the "content" preset:
        (max-width: 768px) 100vw, (max-width: 1200px) 80vw, 800px
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Content image using the "content" responsive context preset for article/blog images.',
      },
    },
  },
};

export const ResponsiveSizesComparison: Story = {
  render: () => (
    <div className="space-y-8 max-w-6xl">
      <div>
        <h3 className="text-lg font-semibold mb-4">Available Responsive Contexts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {Object.entries(RESPONSIVE_SIZES).map(([key, value]) => (
            <div key={key} className="p-4 border border-neutral-200 dark:border-neutral-800 rounded-lg">
              <div className="font-mono font-semibold text-primary-600 dark:text-primary-400 mb-2">
                {key}
              </div>
              <div className="text-neutral-600 dark:text-neutral-400 break-all">
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Overview of all available responsive context presets and their corresponding sizes values.',
      },
    },
  },
};
