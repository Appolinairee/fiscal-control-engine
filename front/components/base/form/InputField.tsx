import React from "react";
import Label from "./Label";
import { cn } from "@/utils/ui/styles";

const InputField = React.forwardRef<HTMLInputElement, InputFieldProps>(
  (
    { label, name, errorMessage, required, className, register, icon, ...rest },
    ref
  ) => {
    return (
      <div className="mb-3">
        {label && (
          <Label title={label} htmlFor={name} icon={icon} required={required} />
        )}

        <input
          id={name}
          name={name}
          ref={ref}
          {...rest}
          {...(register ? register(name) : {})}
          className={cn("input", errorMessage ? "input-error" : "", className)}
        />

        {Boolean(errorMessage) && (
          <p className="input-error-message">{errorMessage}</p>
        )}
      </div>
    );
  }
);

InputField.displayName = "InputField";

export default InputField;
