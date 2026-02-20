import { Button as BootstrapButton } from "react-bootstrap";

// Reuse the actual component type, not just the props
const Button = (props: React.ComponentProps<typeof BootstrapButton>) => {
  return <BootstrapButton {...props} />;
};

export default Button;
