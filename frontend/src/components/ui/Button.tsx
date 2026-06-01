import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { useButtonInteraction } from '@/hooks/useMicroInteraction'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-violet-500 disabled:pointer-events-none disabled:opacity-40 active:scale-[0.97] select-none',
  {
    variants: {
      variant: {
        default:
          'bg-violet-600 text-white hover:bg-violet-500 shadow-sm shadow-violet-900/30',
        destructive:
          'bg-red-600/20 text-red-400 border border-red-500/20 hover:bg-red-600/30 hover:text-red-300',
        outline:
          'border border-white/[0.1] bg-transparent text-white/70 hover:bg-white/[0.06] hover:text-white hover:border-white/[0.18]',
        ghost:
          'bg-transparent text-white/60 hover:bg-white/[0.06] hover:text-white',
        secondary:
          'bg-white/[0.07] text-white/80 hover:bg-white/[0.1] hover:text-white border border-white/[0.06]',
      },
      size: {
        sm: 'h-7 px-2.5 text-[12px] gap-1.5',
        md: 'h-9 px-3.5 text-[13px] gap-2',
        lg: 'h-10 px-5 text-[14px] gap-2',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  interactive?: boolean
  intensity?: 'subtle' | 'medium' | 'strong'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, interactive = true, intensity = 'medium', ...props }, ref) => {
    const { buttonProps } = useButtonInteraction({
      intensity,
      disabled: !interactive || props.disabled,
    })

    return (
      <button
        ref={interactive ? buttonProps.ref : ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...(interactive ? buttonProps : {})}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
