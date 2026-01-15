import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-500 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-amber-600 to-yellow-500 text-amber-950 font-semibold shadow-md hover:from-amber-500 hover:to-yellow-400 hover:shadow-lg hover:shadow-amber-500/20",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-amber-700/50 bg-transparent shadow-sm hover:bg-amber-900/30 hover:border-amber-600/70 text-amber-100",
        secondary:
          "bg-stone-800 text-amber-100 shadow-sm hover:bg-stone-700 border border-stone-700",
        ghost: "hover:bg-amber-900/20 hover:text-amber-100",
        link: "text-amber-400 underline-offset-4 hover:underline hover:text-amber-300",
        gold: "bg-gradient-to-r from-yellow-500 via-amber-400 to-yellow-500 text-amber-950 font-bold shadow-lg hover:shadow-amber-400/30",
        bronze: "bg-gradient-to-r from-orange-700 to-amber-600 text-amber-100 shadow-md hover:from-orange-600 hover:to-amber-500",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        xl: "h-12 rounded-lg px-10 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
